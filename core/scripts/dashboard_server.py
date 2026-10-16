#!/usr/bin/env python3
"""
FreakingJSON PA Framework — Dashboard Server (v0.4.0-beta)

Puente local entre dashboard.html y el framework + opencode.

Qué hace:
  - Sirve el dashboard same-origin (sin CORS, file:// ni fetch roto).
  - Gestiona `opencode serve` (headless) como subprocess: start/stop/status.
  - Proxy de chat/sesiones al API de opencode (verificado en opencode 1.4.6).
  - Edición + preservación (.bak) de core/.context/MASTER.md y profile.md.
  - Diagnóstico del framework (system_check) y bootstrap (session_start).
  - Lanzamiento del TUI opencode externo en una terminal nueva (best effort).
  - API `/api/models/free`: detecta modelos free disponibles.
  - API `/config` POST: guarda configuración (ej. modelo seleccionado).

Esencia respetada: local-first, zero-config, stdlib-only, loopback-only (127.0.0.1).

Uso:
  python core/scripts/dashboard_server.py            # http://127.0.0.1:8760
  python core/scripts/dashboard_server.py --port 9000
"""

import argparse
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
import oc_auth  # noqa: E402  (v0.4.1-beta: detección auth-aware de credenciales)
import select_free_model as sfm  # noqa: E402  (v0.4.1-beta: catálogo usable auth-aware)
import version as framework_version  # noqa: E402
from ensure_data_dirs import ensure_data_dirs  # noqa: E402

OPENCODE_PORT = 47371          # puerto fijo del opencode serve gestionado
SERVER_PORT_DEFAULT = 8760     # puerto del dashboard bridge
EDITABLE_FILE_PATHS = {        # paths relativos al repo configurado
    "master": Path("core/.context/MASTER.md"),
    "profile": Path("core/.context/profile.md"),
}
BRANDING_FILE = Path("config/branding.json")
BRANDING_DEFAULT: dict = {}
BRAND_CACHE: dict[str, tuple[float, dict]] = {}
AGENT_EDIT_ROOTS = {                 # raíces permitidas para edición de agentes
    Path(".opencode") / "agent",
    Path("core") / "agents",
    Path("core") / "agents" / "subagents",
}
AGENT_EDIT_SUFFIXES = {".md"}
AGENT_MAX_BYTES = 512 * 1024         # cap de contenido por documento de agente
def _pa_config_file() -> Path:
    """config.json real del usuario; HOME dinámico para hermeticidad."""
    return Path.home() / ".pa-framework" / "config.json"


SKILLS_INDEXER_SCRIPT = "skills_indexer.py"
MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon",
}

_opencode_proc = {"proc": None, "port": None, "lock": threading.Lock()}


class DashboardHTTPServer(ThreadingHTTPServer):
    """Threaded local server carrying its configured repository root."""

    repo_root: Path
    token_required: bool

    def initialize_token(self) -> str:
        """Load an existing per-install token or create a private one."""
        self._token_lock = threading.RLock()
        self._token_value: str | None = None
        self._token_mtime_ns: int | None = None
        if self.token_path.is_file():
            return self.current_token()
        return self.rotate_token()

    @property
    def token_path(self) -> Path:
        return self.repo_root / "data" / "dashboard.token"

    def current_token(self) -> str:
        """Return the token, reloading it when the token file changes."""
        with self._token_lock:
            if not self.token_path.is_file():
                raise FileNotFoundError(f"dashboard token missing: {self.token_path}")
            mtime_ns = self.token_path.stat().st_mtime_ns
            if self._token_value is None or self._token_mtime_ns != mtime_ns:
                token = self.token_path.read_text(encoding="utf-8").strip()
                if len(token) < 32:
                    return self.rotate_token()
                self._token_value = token
                self._token_mtime_ns = mtime_ns
            return self._token_value

    def rotate_token(self) -> str:
        """Atomically replace the token and revoke the cached value."""
        with self._token_lock:
            token = secrets.token_urlsafe(32)
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.token_path.with_name(
                f".{self.token_path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
            )
            fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(token + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(tmp_path, 0o600)
                os.replace(tmp_path, self.token_path)
                os.chmod(self.token_path, 0o600)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
            self._token_value = token
            self._token_mtime_ns = self.token_path.stat().st_mtime_ns
            return token


# ---------------------------------------------------------------- helpers ---
def log(msg: str) -> None:
    print(f"[pa-dashboard] {msg}", flush=True)


def oc_base() -> str:
    return f"http://127.0.0.1:{_opencode_proc.get('port') or OPENCODE_PORT}"


def oc_call(path: str, method: str = "GET", body: dict | None = None,
            timeout: int = 120) -> tuple[int, object]:
    """Llamada al API de opencode. Devuelve (status, json|error_str)."""
    url = oc_base() + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, method=method, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                return r.status, json.loads(raw or "null")
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "null")
        except Exception:
            return e.code, {}
    except Exception as e:  # connection refused, timeout…
        return -1, str(e)


def opencode_installed() -> str | None:
    exe = shutil.which("opencode")
    if exe:
        return exe
    # fallback: instalación estándar de opencode (~/.opencode/bin)
    home_bin = Path.home() / ".opencode" / "bin"
    for name in ("opencode", "opencode.exe", "opencode.cmd"):
        cand = home_bin / name
        if cand.exists():
            return str(cand)
    return None


def opencode_serving() -> bool:
    st, _ = oc_call("/global/health", timeout=5)
    return st == 200


def free_port(preferred: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def opencode_ensure() -> dict:
    """Arranca `opencode serve` si no está corriendo. Idempotente."""
    with _opencode_proc["lock"]:
        if opencode_serving():
            return {"ok": True, "already": True, "port": _opencode_proc.get("port") or OPENCODE_PORT}
        exe = opencode_installed()
        if not exe:
            return {"ok": False, "error": "opencode no está instalado (npm install -g opencode-ai)"}
        # QAWIN-RUNTIME: gate de versión fail-closed antes de spawnear serve.
        ver_ok, ver_msg = sfm.enforce_opencode_version(exe)
        if not ver_ok:
            return {"ok": False, "error": ver_msg}
        port = free_port(OPENCODE_PORT)
        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = subprocess.Popen(
            [exe, "serve", "--port", str(port), "--hostname", "127.0.0.1"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        _opencode_proc["proc"], _opencode_proc["port"] = proc, port
        # esperar readiness (máx ~15s)
        for _ in range(30):
            time.sleep(0.5)
            if opencode_serving():
                return {"ok": True, "already": False, "port": port}
            if proc.poll() is not None:
                return {"ok": False, "error": f"opencode serve murió (exit {proc.returncode})"}
        return {"ok": False, "error": "opencode serve no respondió a tiempo"}


def run_py(script: str, *args: str, timeout: int = 90) -> dict:
    """Ejecuta un script del framework y devuelve {ok, output}."""
    s = SCRIPT_DIR / script
    if not s.exists():
        return {"ok": False, "output": f"script no encontrado: {script}"}
    try:
        r = subprocess.run([sys.executable, str(s), *args], cwd=str(REPO_ROOT),
                           capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + (r.stderr or "")
        return {"ok": r.returncode == 0, "output": out[-8000:]}
    except Exception as e:
        return {"ok": False, "output": str(e)}


# ------------------------------------------------- dashboard command center ---
def load_brand(repo_root: Path) -> dict:
    """Lee config/branding.json del repo trackeado (con cache por mtime).

    Nunca lanza: branding corrupto → {} y /api/status sigue vivo. Defaults
    no invaden la respuesta: si falta el archivo no se inventan datos.
    """
    path = repo_root / BRANDING_FILE
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        return dict(BRANDING_DEFAULT)
    cached = BRAND_CACHE.get(str(path))
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = dict(BRANDING_DEFAULT)
    except Exception:
        data = dict(BRANDING_DEFAULT)
    BRAND_CACHE[str(path)] = (mtime, data)
    return data


def _load_json_index(path: Path) -> object:
    """Lee un índice JSON; devuelve None ante missing/malformed."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _entries(data: object, key: str) -> list:
    """Lista de entries dict de un índice; shape raro → []."""
    if not isinstance(data, dict):
        return []
    entries = data.get(key)
    return entries if isinstance(entries, list) else []


def _atomic_write_json_0600(path: Path, payload: object) -> None:
    """Escribe JSON privado de forma atómica, sin dejar temporales."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    finally:
        if tmp.exists():
            tmp.unlink()


def knowledge_summary(repo_root: Path) -> dict:
    """Resumen whitelisted de los índices de conocimiento (sin cuerpos).

    Metadatos only: ids, fechas, títulos, contadores. Nunca summary/content/
    highlights/file_path — nada de rutas absolutas ni secretos.
    """
    kdir = repo_root / "core" / ".context" / "knowledge"

    sessions: list[dict] = []
    raw = _load_json_index(kdir / "sessions-index.json")
    for s in _entries(raw, "sessions"):
        if not isinstance(s, dict):
            continue
        session = {k: s[k] for k in ("id", "date", "title", "topics") if k in s}
        if session:
            sessions.append(session)

    interactions: list[dict] = []
    raw = _load_json_index(kdir / "interactions-index.json")
    for i in _entries(raw, "interactions"):
        if not isinstance(i, dict):
            continue
        event = {k: i[k] for k in ("tool", "count") if k in i}
        if event:
            interactions.append(event)

    skills: list[dict] = []
    raw = _load_json_index(kdir / "skills-index.json")
    for s in _entries(raw, "skills"):
        if not isinstance(s, dict):
            continue
        skill = {k: s[k] for k in ("id", "name", "category") if k in s}
        if skill:
            skills.append(skill)

    agents: list[dict] = []
    raw = _load_json_index(kdir / "agents-index.json")
    for a in _entries(raw, "agents"):
        if not isinstance(a, dict):
            continue
        location = a.get("location")
        entry = {k: a[k] for k in ("name", "type", "description", "location",
                                   "status") if k in a}
        entry["editable"] = bool(location and
                                 resolve_agent_document(repo_root, location))
        agents.append(entry)

    errors: list[dict] = []
    raw = _load_json_index(kdir / "errors" / "index.json")
    for e in (raw if isinstance(raw, list) else
              _entries(raw, "errors")):
        if not isinstance(e, dict):
            continue
        entry = {k: e[k] for k in ("id", "timestamp", "type", "severity") if k in e}
        if entry:
            errors.append(entry)

    return {
        "ok": True,
        "sessions": sessions,
        "interactions": interactions,
        "skills": skills,
        "agents": agents,
        "errors": errors,
        "counts": {
            "sessions": len(sessions),
            "interactions": len(interactions),
            "skills": len(skills),
            "agents": len(agents),
            "errors": len(errors),
        },
    }


def agent_document_path(repo_root: Path, location: str) -> Path:
    """Resuelve la ruta de un documento de agente o lanza ValueError.

    Contención estricta: relativo, sin traversal, suffix .md y dentro de
    AGENT_EDIT_ROOTS. (root / location) — jamás rutas absolutas del índice.
    """
    if not isinstance(location, str) or not location.strip():
        raise ValueError("location vacía")
    if "\\" in location:
        raise ValueError("separador backslash no permitido")
    candidate = Path(location)
    if candidate.is_absolute() or candidate.drive or candidate.root:
        raise ValueError("ruta absoluta no permitida")
    if candidate.suffix.lower() not in AGENT_EDIT_SUFFIXES:
        raise ValueError("solo documentos .md")
    if any(part == ".." for part in candidate.parts):
        raise ValueError("traversal no permitido")
    resolved = (repo_root / candidate).resolve()
    allowed = [((repo_root / root).resolve(), root) for root in AGENT_EDIT_ROOTS]
    for root_resolved, root in allowed:
        try:
            resolved.relative_to(root_resolved)
        except ValueError:
            continue
        return repo_root / candidate
    raise ValueError("documento fuera de las raíces de edición")


def resolve_agent_document(repo_root: Path, location: str) -> Path | None:
    """Ruta real de un documento de agente editable; None si no aplica."""
    try:
        path = agent_document_path(repo_root, location)
    except (ValueError, OSError):
        return None
    try:
        if path.is_symlink() or not path.is_file():
            return None
        if path.resolve() != path:
            return None
    except OSError:
        return None
    if path.stat().st_size > AGENT_MAX_BYTES:
        return None
    return path


def agent_editable_from_index(repo_root: Path, agents: object) -> set[str]:
    """Ids/nombres de agentes con documento index-backed editable."""
    editable: set[str] = set()
    for entry in _entries(agents, "agents"):
        if not isinstance(entry, dict):
            continue
        location = entry.get("location")
        name = entry.get("name") or entry.get("id")
        if isinstance(location, str) and isinstance(name, str) and \
                resolve_agent_document(repo_root, location):
            editable.add(name)
    return editable


def agent_index_by_id(repo_root: Path) -> dict[str, dict]:
    """Mapa id/nombre → entry del agents-index actual (solo reales)."""
    raw = _load_json_index(
        repo_root / "core" / ".context" / "knowledge" / "agents-index.json")
    mapping: dict[str, dict] = {}
    for entry in _entries(raw, "agents"):
        if not isinstance(entry, dict):
            continue
        for key in ("name", "id"):
            value = entry.get(key)
            if isinstance(value, str) and value:
                mapping[value] = entry
    return mapping


def update_agent_document(repo_root: Path, agent_id: str, content: object) -> int:
    """Escribe un documento de agente con backup timestamped.

    Devuelve 0 en éxito o el código HTTP que corresponde al rechazo.
    Nunca toca credenciales ni core/.context: la contención vive en
    agent_document_path() y resolve_agent_document().
    """
    if not isinstance(content, str):
        return 400
    if len(content.encode("utf-8")) > AGENT_MAX_BYTES:
        return 413
    entry = agent_index_by_id(repo_root).get(agent_id)
    if entry is None:
        return 404  # id no indexado
    location = entry.get("location")
    if not isinstance(location, str):
        return 400
    try:
        path = agent_document_path(repo_root, location)
    except ValueError:
        return 400
    if path.is_symlink() or not path.is_file():
        return 400
    try:
        if path.resolve() != path:
            return 400  # symlink (aunque apunte dentro del repo)
        if path.stat().st_size > AGENT_MAX_BYTES:
            return 413
        backup = path.with_name(
            f"{path.name}.bak-{datetime.now():%Y%m%d-%H%M%S}")
        shutil.copy2(path, backup)
        path.write_text(content, encoding="utf-8")
    except OSError:
        return 500
    return 0


def read_agent_document(repo_root: Path, agent_id: str) -> tuple[int, dict]:
    """Lee un documento de agente index-backed (contención estricta)."""
    entry = agent_index_by_id(repo_root).get(agent_id)
    if entry is None:
        return 404, {}
    location = entry.get("location")
    if not isinstance(location, str):
        return 400, {}
    try:
        path = agent_document_path(repo_root, location)
    except ValueError:
        return 400, {}
    if path.is_symlink() or not path.is_file():
        return 400, {}
    try:
        if path.resolve() != path:
            return 400, {}
        if path.stat().st_size > AGENT_MAX_BYTES:
            return 413, {}
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 500, {}
    return 0, {"ok": True, "id": agent_id,
               "path": path.relative_to(repo_root).as_posix(),
               "content": content}


def toggle_skill(repo_root: Path, skill_id: object, enabled: object) -> tuple[int, dict]:
    """Activa/desactiva una skill en ~/.pa-framework/config.json (atómico).

    Valida el id contra el skills-index actual, preserva claves desconocidas
    y fuerza chmod 0600. Devuelve (status, payload).
    """
    if not isinstance(skill_id, str) or not skill_id.strip():
        return 400, {"ok": False, "error": "id requerido"}
    if not isinstance(enabled, bool):
        return 400, {"ok": False, "error": "enabled debe ser booleano"}
    raw = _load_json_index(
        repo_root / "core" / ".context" / "knowledge" / "skills-index.json")
    known = {s.get("id") for s in _entries(raw, "skills")
             if isinstance(s, dict) and isinstance(s.get("id"), str)}
    if skill_id not in known:
        return 404, {"ok": False, "error": f"skill no indexada: {skill_id}"}
    try:
        config_file = _pa_config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config: dict = {}
        if config_file.exists():
            try:
                loaded = json.loads(config_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    config = loaded
            except Exception:
                config = {}
        current = config.get("enabled_skills")
        enabled_skills = [s for s in current if isinstance(s, str)] \
            if isinstance(current, list) else []
        if enabled:
            if skill_id not in enabled_skills:
                enabled_skills.append(skill_id)
        else:
            enabled_skills = [s for s in enabled_skills if s != skill_id]
        config["enabled_skills"] = enabled_skills
        _atomic_write_json_0600(config_file, config)
    except OSError as exc:
        return 500, {"ok": False, "error": str(exc)}
    return 200, {"ok": True, "enabled_skills": enabled_skills}


def launch_opencode_tui() -> dict:
    """Abre el TUI de opencode en una terminal nueva del SO (best effort).

    v0.4.1-beta: lanza con el AGENTE y MODELO asignados por el framework
    (leídos de .opencode/config.json). Antes lanzaba opencode pelado →
    el TUI arrancaba con el default global de la máquina, ignorando la
    asignación del framework (bug N30 2026-08-19).
    """
    exe = opencode_installed()
    if not exe:
        return {"ok": False, "error": "opencode no está instalado"}
    # QAWIN-RUNTIME: gate de versión fail-closed antes de abrir la TUI.
    ver_ok, ver_msg = sfm.enforce_opencode_version(exe)
    if not ver_ok:
        return {"ok": False, "error": ver_msg}
    # QAWIN-RUNTIME: modelo desde la selección canónica del usuario; el agente
    # sigue siendo parte del config OpenCode compatible con v0.4.0.
    agent_flags = []
    try:
        selection = sfm.load_selection(REPO_ROOT)
    except Exception:
        selection = {}
    model = selection.get("model")
    try:
        cfg = json.loads(
            (REPO_ROOT / ".opencode" / "config.json").read_text(encoding="utf-8")
        )
    except Exception:
        cfg = {}
    if not model:
        model = cfg.get("model")
    agent = cfg.get("agent")
    if agent:
        agent_flags += ["--agent", str(agent)]
    if model and model != "auto":
        agent_flags += ["--model", str(model)]
    try:
        if sys.platform == "win32":
            # QAWIN-RUNTIME: consola nueva SIN shell=True — cmd.exe con
            # lista argv ('start' como argumento), cero interpolación.
            subprocess.Popen(
                ["cmd.exe", "/d", "/s", "/c", "start", "FreakingJSON PA — opencode",
                 "/D", str(REPO_ROOT), exe, *agent_flags],
                cwd=str(REPO_ROOT),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "Terminal", exe], cwd=str(REPO_ROOT))
        else:
            term = next((t for t in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm")
                         if shutil.which(t)), None)
            if not term:
                return {"ok": False, "error": "ninguna terminal conocida (x-terminal-emulator/gnome-terminal/konsole/xterm)"}
            subprocess.Popen([term, "-e", f'cd "{REPO_ROOT}" && "{exe}" {" ".join(agent_flags)}'])
        hint = "TUI lanzada en terminal externa"
        if agent_flags:
            hint += " con " + " ".join(agent_flags)
        return {"ok": True, "hint": hint}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _win_quote(s: str) -> str:
    """Comilla un argumento para cmd.exe (solo si contiene espacios)."""
    return f'"{s}"' if (" " in s or "\t" in s) else s


# ---------------------------------------------------------------- handler ---
class Handler(BaseHTTPRequestHandler):
    server_version = f"PA-Dashboard/{framework_version.canonical(REPO_ROOT)}"

    # ---- plumbing ----
    @property
    def repo_root(self) -> Path:
        """Repository root configured for this server instance."""
        return Path(getattr(self.server, "repo_root", REPO_ROOT))

    @property
    def editable_files(self) -> dict[str, Path]:
        return {key: self.repo_root / relative
                for key, relative in EDITABLE_FILE_PATHS.items()}

    def _guard_loopback_origin(self) -> bool:
        """Require a loopback Host and reject foreign browser origins."""
        server = cast(DashboardHTTPServer, self.server)
        port = int(server.server_address[1])
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = (self.headers.get("Host") or "").strip().lower()
        if host not in allowed_hosts:
            self._json({"ok": False, "error": "invalid host"}, 403)
            return False

        origin = (self.headers.get("Origin") or "").strip().lower().rstrip("/")
        allowed_origins = {f"http://{candidate}" for candidate in allowed_hosts}
        if origin and origin not in allowed_origins:
            self._json({"ok": False, "error": "invalid origin"}, 403)
            return False
        return True

    def _guard_mutation(self) -> bool:
        """Validate same-origin token-authenticated JSON mutations."""
        if not self._guard_loopback_origin():
            return False

        server = cast(DashboardHTTPServer, self.server)
        token_required = bool(server.token_required)
        supplied = self.headers.get("X-PA-Token") or ""
        try:
            expected = server.current_token() if token_required else ""
        except OSError:
            self._json({"ok": False, "error": "dashboard token unavailable"}, 503)
            return False
        if token_required and not secrets.compare_digest(supplied, expected):
            self._json({"ok": False, "error": "invalid token"}, 401)
            return False

        content_type = (self.headers.get("Content-Type") or "").split(";", 1)[0]
        if content_type.strip().lower() != "application/json":
            self._json({"ok": False, "error": "application/json required"}, 415)
            return False
        return True

    def _json(self, obj: object, status: int = 200) -> None:
        data = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception:
            return {}

    def log_message(self, format, *args):  # silencio, log propio
        pass

    # ---- GET ----
    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/" or path == "/index.html":
            return self._serve_file(self.repo_root / "dashboard.html")
        if path == "/api/security/token":
            if not self._guard_loopback_origin():
                return
            server = cast(DashboardHTTPServer, self.server)
            try:
                return self._json({"token": server.current_token()})
            except OSError:
                return self._json({"error": "dashboard token unavailable"}, 503)
        if path == "/api/status":
            return self._json({
                "framework": {
                    "version": framework_version.canonical(self.repo_root),
                    "brand": load_brand(self.repo_root),
                },
                "opencode": {
                    "installed": bool(opencode_installed()),
                    "serving": opencode_serving(),
                    "port": _opencode_proc.get("port") or OPENCODE_PORT,
                },
            })
        if path == "/api/knowledge/summary":
            if not self._guard_loopback_origin():
                return
            return self._json(knowledge_summary(self.repo_root))
        if path == "/api/agents/list":
            if not self._guard_loopback_origin():
                return
            agents = agent_index_by_id(self.repo_root)
            # dedup preservando orden de índice (name+id pueden duplicar)
            seen: set[str] = set()
            listing: list[dict] = []
            for entry in agents.values():
                name = entry.get("name") or entry.get("id") or ""
                if not isinstance(name, str) or name in seen:
                    continue
                seen.add(name)
                location = entry.get("location")
                item: dict = {"name": name}
                for field in ("type", "description", "location", "status"):
                    value = entry.get(field)
                    if isinstance(value, str):
                        item[field] = value
                item["editable"] = bool(isinstance(location, str) and
                                        resolve_agent_document(self.repo_root,
                                                               location))
                listing.append(item)
            return self._json({"ok": True, "agents": listing})
        if path == "/api/agents/read":
            # Contenido de agentes: token SIEMPRE (mutation-grade guard en GET)
            if not self._guard_mutation():
                return
            agent_id = (urllib.parse.parse_qs(self.path.split("?", 1)[-1])
                        .get("id") or [""])[0]
            status, payload = read_agent_document(self.repo_root, agent_id)
            return self._json(payload, status or 200)
        if path == "/api/opencode/sessions":
            if not opencode_serving():
                return self._json({"ok": False, "error": "opencode serve no activo"}, 503)
            st, data = oc_call("/session")
            return self._json({"ok": st == 200, "sessions": data if st == 200 else None,
                               "error": None if st == 200 else data}, 200 if st == 200 else 502)
        if path.startswith("/api/opencode/messages/"):
            sid = path.rsplit("/", 1)[-1]
            st, data = oc_call(f"/session/{sid}/message")
            return self._json({"ok": st == 200, "messages": data if st == 200 else None,
                               "error": None if st == 200 else data}, 200 if st == 200 else 502)
        if path == "/api/files/config":
            out = {"ok": True, "files": {}}
            for key, p in self.editable_files.items():
                out["files"][key] = {
                    "path": str(p.relative_to(self.repo_root)),
                    "exists": p.exists(),
                    "content": p.read_text(encoding="utf-8", errors="replace") if p.exists() else "",
                }
            return self._json(out)
        if path in {"/api/framework/check", "/api/framework/bootstrap", "/api/models/test"}:
            return self._json({"error": "method not allowed", "method": "POST"}, 405)
        if path == "/api/skills/toggle":
            return self._json({"error": "method not allowed", "method": "POST"}, 405)
        
        if path == "/api/models/free":
            # Lectura pura: nunca inicia procesos. Si serve está apagado, retorna [].
            # Dashboard command center (D1): SOLO modelos free vía sfm.get_free_models.
            # Detección != uso: para probar/usar cualquier modelo existe /test.
            port = _opencode_proc.get("port") or OPENCODE_PORT
            # QAWIN-RUNTIME/Dashboard D1: solo modelos free en superficies de PA.
            models = sfm.get_free_models(port)
            models_payload = [
                {"id": m["id"], "status": m["status"],
                 "badge": oc_auth.provider_auth_badge(m["status"]), "free": True}
                for m in models
            ]
            return self._json(models_payload)


        if path == "/api/config/model":
            # La selección mutable vive en data/user; agent conserva lectura legacy.
            selection = sfm.load_selection(self.repo_root)
            legacy = {}
            legacy_path = self.repo_root / ".opencode" / "config.json"
            if legacy_path.exists():
                try:
                    value = json.loads(legacy_path.read_text(encoding="utf-8"))
                    legacy = value if isinstance(value, dict) else {}
                except Exception:
                    legacy = {}
            return self._json({
                "ok": True,
                "model": selection.get("model") or "",
                "agent": selection.get("agent") or legacy.get("agent") or "",
            })

        # Estáticos públicos exclusivamente. Nunca exponer context/data/config,
        # dotfiles, traversal codificado ni symlinks.
        decoded = urllib.parse.unquote(path).replace("\\", "/")
        rel = decoded.lstrip("/")
        parts = Path(rel).parts
        static_allowed = bool(parts and parts[0] in {"core", "assets", "docs"})
        static_denied = (
            any(part in {"", ".", ".."} or part.startswith(".") for part in parts)
            or (parts and parts[0] == "core" and len(parts) > 1
                and parts[1] == ".context")
        )
        if static_allowed and not static_denied:
            return self._serve_file(self.repo_root / Path(*parts))
        self._json({"error": "not found", "path": path}, 404)

    # ---- POST ----
    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/api/") and not self._guard_mutation():
            return
        body = self._body()

        if path == "/api/runtime/ensure":
            return self._json(opencode_ensure())

        if path == "/api/framework/check":
            return self._json(run_py("system_check.py", "--quick", timeout=60))

        if path == "/api/framework/bootstrap":
            return self._json(run_py("session_start.py", timeout=90))

        if path == "/api/models/test":
            mid_param = str(body.get("model") or "").strip()
            if not mid_param:
                return self._json({"ok": False, "error": "model requerido"}, 400)
            if not opencode_serving():
                return self._json({"ok": False, "error": "runtime no activo"}, 503)
            provider_id, _, model_name = mid_param.partition("/")
            if not model_name:
                return self._json({"ok": False, "error": "formato provider/model"}, 400)
            st, sess = oc_call("/session", "POST", {"title": "PA model test"})
            if st != 200 or not isinstance(sess, dict):
                return self._json({"ok": False, "error": f"crear sesión: {sess}"}, 502)
            sid = sess.get("id")
            st, resp = oc_call(
                f"/session/{sid}/message", "POST",
                {"parts": [{"type": "text", "text": "ping"}],
                 "model": {"providerID": provider_id, "modelID": model_name}},
                timeout=60,
            )
            info = resp.get("info", {}) if isinstance(resp, dict) else {}
            used = f"{info.get('providerID')}/{info.get('modelID')}"
            ok = st == 200 and info.get("modelID") == model_name
            return self._json({
                "ok": ok,
                "status": st,
                "used_model": used,
                "requested": mid_param,
                "error": None if ok else (resp if not isinstance(resp, dict) else resp.get("error")),
            })

        if path == "/api/opencode/chat":
            msg = (body.get("message") or "").strip()
            if not msg:
                return self._json({"ok": False, "error": "mensaje vacío"}, 400)
            if not opencode_serving():
                return self._json({"ok": False, "error": "runtime no activo"}, 503)
            sid = body.get("session")
            if not sid:
                st, sess = oc_call("/session", "POST", {"title": body.get("title") or "PA Dashboard"})
                if st != 200 or not isinstance(sess, dict):
                    return self._json({"ok": False, "error": f"crear sesión: {sess}"}, 502)
                sid = sess.get("id")
            # v0.4.1-beta (fix bug N30 2026-08-19): el chat debe usar el MODELO
            # ASIGNADO por el framework, no el default global de opencode.
            # Antes: send() del dashboard no enviaba model y este endpoint lo
            # ignoraba → el chat respondía con el default de la máquina
            # (ej. glm-4.7 global) aunque el usuario hubiera "asignado" otro.
            # Además la API serve de opencode EXIGE objeto {providerID, modelID}
            # (string crudo → HTTP 400), y "agentID" NO está soportado en serve
            # 1.4.6 (se ignora). El agente FreakingJSON solo puede forzarse
            # vía CLI (--agent), no vía serve.
            model = body.get("model")
            if not model:
                # fallback: selección local generada, nunca el config trackeado.
                model = sfm.load_selection(self.repo_root).get("model") or None
            payload: dict = {"parts": [{"type": "text", "text": msg}]}
            if model:
                # normalizar a objeto — la API serve rechaza strings (400)
                if isinstance(model, str):
                    pid, _, mid = model.partition("/")
                    model = {"providerID": pid, "modelID": mid} if mid else None
                if model:
                    payload["model"] = model
            st, resp = oc_call(f"/session/{sid}/message", "POST", payload, timeout=180)
            if st != 200:
                return self._json({"ok": False, "error": f"opencode: {resp}", "session": sid}, 502)
            # extraer texto de la respuesta
            texts = []
            info = {}
            if isinstance(resp, dict):
                info = resp.get("info", {}) or {}
                texts = [p.get("text", "") for p in resp.get("parts", []) if p.get("type") == "text"]
            used = f"{info.get('providerID')}/{info.get('modelID')}" if info.get("modelID") else ""
            return self._json({"ok": True, "session": sid,
                               "reply": "\n".join(t for t in texts if t).strip(),
                               "model_used": used})

        if path == "/api/files/config":
            key = body.get("file")
            content = body.get("content", "")
            editable_files = self.editable_files
            if key not in editable_files:
                return self._json({"ok": False, "error": f"archivo no editable: {key}"}, 400)
            p = editable_files[key]
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists():  # preservación: .bak con timestamp
                bak = p.with_suffix(p.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
                shutil.copy2(p, bak)
            p.write_text(content, encoding="utf-8")
            return self._json({"ok": True, "saved": str(p.relative_to(self.repo_root))})

        if path == "/api/config/model":
            # Estado generado local: no mutar .opencode/config.json trackeado.
            model = (body.get("model") or "").strip()
            if not model:
                return self._json({"ok": False, "error": "model vacío"}, 400)
            sfm.save_selection(model, self.repo_root)
            return self._json({
                "ok": True,
                "model": model,
                "saved": "data/user/model-selection.json",
            })

        if path == "/api/skills/toggle":
            status, payload = toggle_skill(
                self.repo_root, body.get("id"), body.get("enabled"))
            return self._json(payload, status)

        if path == "/api/skills/reindex":
            # Solo skills_indexer.py: el body NO puede elegir script (fijo).
            return self._json(run_py(SKILLS_INDEXER_SCRIPT, timeout=120))

        if path == "/api/agents/update":
            agent_id = body.get("id")
            if not isinstance(agent_id, str) or not agent_id.strip():
                return self._json({"ok": False, "error": "id requerido"}, 400)
            status = update_agent_document(
                self.repo_root, agent_id, body.get("content"))
            if status == 0:
                return self._json({"ok": True, "id": agent_id,
                                   "saved": True})
            return self._json({"ok": False, "error": f"agent update rejected ({status})"},
                              status)

        if path == "/api/launch/opencode-tui":
            # bootstrap del framework ANTES de abrir la TUI (flujo base completo)
            run_py("session_start.py", timeout=90)
            return self._json(launch_opencode_tui())

        self._json({"error": "not found", "path": path}, 404)

    # ---- static ----
    def _serve_file(self, f: Path):
        try:
            root = self.repo_root.resolve()
            candidate = f.resolve(strict=True)
            candidate.relative_to(root)
            relative = f.relative_to(self.repo_root)
            current = self.repo_root
            for part in relative.parts:
                current = current / part
                if current.is_symlink():
                    raise ValueError("symlinked static path")
        except (OSError, ValueError):
            return self._json({"error": "not found"}, 404)
        if not candidate.is_file():
            return self._json({"error": "not found"}, 404)
        data = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(candidate.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        # v0.5.0: no-cache para que el browser siempre pida el HTML/JS fresco
        # (evita que una extracción vieja siga sirviendo JS roto desde cache)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)


# ------------------------------------------------------------------- main ---
def make_server(host: str = "127.0.0.1", port: int = 0,
                repo_root: str | Path | None = None,
                token_required: bool = True) -> tuple[DashboardHTTPServer, int]:
    """Create a dashboard server without starting its serving loop."""
    srv = DashboardHTTPServer((host, port), Handler)
    try:
        srv.repo_root = Path(repo_root or REPO_ROOT).resolve()
        srv.token_required = token_required
        ensure_data_dirs(srv.repo_root)
        sfm.load_selection(srv.repo_root)
        srv.initialize_token()
    except Exception:
        srv.server_close()
        raise
    return srv, int(srv.server_address[1])


def main():
    ap = argparse.ArgumentParser(description="PA Framework Dashboard Server")
    ap.add_argument("--port", type=int, default=SERVER_PORT_DEFAULT)
    ap.add_argument("--host", default="127.0.0.1",
                    help="loopback-only por defecto (local-first)")
    args = ap.parse_args()

    srv, port = make_server(args.host, args.port)
    log(f"http://{args.host}:{port}  (Ctrl+C para detener)")
    log(f"repo: {srv.repo_root}")
    if opencode_installed():
        log(f"opencode: {opencode_installed()} (serve se arranca vía POST /api/runtime/ensure)")
    else:
        log("opencode: NO detectado — chat no disponible hasta instalarlo")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        log("deteniendo…")
    finally:
        proc = _opencode_proc.get("proc")
        if proc and proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    main()

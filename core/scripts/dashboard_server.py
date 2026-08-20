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
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
import oc_auth  # noqa: E402  (v0.4.1-beta: detección auth-aware de credenciales)
import select_free_model as sfm  # noqa: E402  (v0.4.1-beta: catálogo usable auth-aware)

OPENCODE_PORT = 47371          # puerto fijo del opencode serve gestionado
SERVER_PORT_DEFAULT = 8760     # puerto del dashboard bridge
EDITABLE_FILES = {             # archivos .md editables desde el dashboard
    "master": CORE_DIR / ".context" / "MASTER.md",
    "profile": CORE_DIR / ".context" / "profile.md",
}
MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon",
}

_opencode_proc = {"proc": None, "port": None, "lock": threading.Lock()}


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
    # flags de agente/modelo desde la asignación del framework
    agent_flags = []
    cfg_path = REPO_ROOT / ".opencode" / "config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            agent = cfg.get("agent")
            if agent:
                agent_flags += ["--agent", str(agent)]
            model = cfg.get("model")
            if model and model != "auto":
                agent_flags += ["--model", str(model)]
        except Exception:
            pass
    try:
        if sys.platform == "win32":
            # 'start' abre consola nueva; /k la mantiene viva
            flags = " ".join(_win_quote(a) for a in agent_flags)
            subprocess.Popen(f'start "FreakingJSON PA — opencode" /D "{REPO_ROOT}" "{exe}" {flags}',
                             shell=True, cwd=str(REPO_ROOT))
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
    server_version = "PA-Dashboard/0.4.1-beta"

    # ---- plumbing ----
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
            return self._serve_file(REPO_ROOT / "dashboard.html")
        if path == "/api/status":
            return self._json({
                "framework": {
                    "version": (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
                               if (REPO_ROOT / "VERSION").exists() else "?",
                },
                "opencode": {
                    "installed": bool(opencode_installed()),
                    "serving": opencode_serving(),
                    "port": _opencode_proc.get("port") or OPENCODE_PORT,
                },
            })
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
            for key, p in EDITABLE_FILES.items():
                out["files"][key] = {
                    "path": str(p.relative_to(REPO_ROOT)),
                    "exists": p.exists(),
                    "content": p.read_text(encoding="utf-8", errors="replace") if p.exists() else "",
                }
            return self._json(out)
        if path == "/api/framework/check":
            return self._json(run_py("system_check.py", "--quick", timeout=60))
        if path == "/api/framework/bootstrap":
            return self._json(run_py("session_start.py", timeout=90))
        
        if path == "/api/models/free":
            # Detectar modelos desde opencode serve (auto-inicia si es necesario)
            # v0.4.1-beta (feedback N30): AUTH-AWARE y COMPLETO — lista TODO el
            # catálogo de proveedores con credenciales (free + paid, ej. minimax
            # configurado) + los free del resto. Nada bloqueado: sin-creds van
            # al final con badge. Detectar != usar — para eso existe /test.
            r = opencode_ensure()
            if not r.get("ok"):
                return self._json({"ok": False, "error": r.get("error", "opencode no disponible")}, 503)
            models = sfm.get_usable_models(r["port"])
            models_payload = [
                {"id": m["id"], "status": m["status"], "badge": oc_auth.provider_auth_badge(m["status"]), "free": m.get("free", True)}
                for m in models
            ]
            # cred-first ya garantizado por get_usable_models
            return self._json(models_payload)

        if path == "/api/models/test":
            # v0.4.1-beta: ping REAL del modelo seleccionado — verifica que la
            # credencial FUNCIONA (no solo que existe). Un modelo "detectado"
            # sin creds que funcione es exactamente el bug reportado.
            q = path  # solo GET
            model_id = (self.path.split("?", 1)[1] if "?" in self.path else "")
            from urllib.parse import parse_qs
            params = parse_qs(model_id)
            mid_param = (params.get("model", [""])[0] or "").strip()
            if not mid_param:
                return self._json({"ok": False, "error": "parámetro model requerido"}, 400)
            ensure = opencode_ensure()
            if not ensure.get("ok"):
                return self._json({"ok": False, "error": ensure.get("error")}, 503)
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

        if path == "/api/config/model":
            # v0.4.0-beta: modelo ACTUAL desde .opencode/config.json (sin exponer el archivo crudo)
            cfg_path = REPO_ROOT / ".opencode" / "config.json"
            cfg = {}
            if cfg_path.exists():
                try:
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {}
            return self._json({
                "ok": True,
                "model": cfg.get("model") or "",
                "agent": cfg.get("agent") or "",
            })

        # estáticos: dashboard-data.js, knowledge indexes, assets
        rel = path.lstrip("/")
        if rel.startswith(("dashboard-data.js", "core/", "assets/", "docs/")):
            return self._serve_file(REPO_ROOT / rel)
        self._json({"error": "not found", "path": path}, 404)

    # ---- POST ----
    def do_POST(self):
        path = self.path.split("?", 1)[0]
        body = self._body()

        if path == "/api/opencode/ensure":
            return self._json(opencode_ensure())

        if path == "/api/opencode/chat":
            msg = (body.get("message") or "").strip()
            if not msg:
                return self._json({"ok": False, "error": "mensaje vacío"}, 400)
            ensure = opencode_ensure()
            if not ensure.get("ok"):
                return self._json(ensure, 503)
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
                # fallback: modelo guardado en .opencode/config.json (asignación del framework)
                cfg_path = REPO_ROOT / ".opencode" / "config.json"
                if cfg_path.exists():
                    try:
                        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                        model = cfg.get("model") or None
                    except Exception:
                        model = None
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
            if key not in EDITABLE_FILES:
                return self._json({"ok": False, "error": f"archivo no editable: {key}"}, 400)
            p = EDITABLE_FILES[key]
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists():  # preservación: .bak con timestamp
                bak = p.with_suffix(p.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
                shutil.copy2(p, bak)
            p.write_text(content, encoding="utf-8")
            return self._json({"ok": True, "saved": str(p.relative_to(REPO_ROOT))})

        if path == "/api/config/model":
            # v0.5.0: guardar modelo predeterminado en .opencode/config.json (con backup)
            model = (body.get("model") or "").strip()
            if not model:
                return self._json({"ok": False, "error": "model vacío"}, 400)
            cfg_path = REPO_ROOT / ".opencode" / "config.json"
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            cfg = {}
            if cfg_path.exists():
                try:
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {}
            if cfg_path.exists():
                bak = cfg_path.with_suffix(cfg_path.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
                shutil.copy2(cfg_path, bak)
            cfg["model"] = model
            cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            return self._json({"ok": True, "model": model, "saved": ".opencode/config.json"})

        if path == "/api/launch/opencode-tui":
            # bootstrap del framework ANTES de abrir la TUI (flujo base completo)
            run_py("session_start.py", timeout=90)
            return self._json(launch_opencode_tui())

        self._json({"error": "not found", "path": path}, 404)

    # ---- static ----
    def _serve_file(self, f: Path):
        if not f.is_file():
            return self._json({"error": "not found"}, 404)
        data = f.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(f.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        # v0.5.0: no-cache para que el browser siempre pida el HTML/JS fresco
        # (evita que una extracción vieja siga sirviendo JS roto desde cache)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)


# ------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser(description="PA Framework Dashboard Server")
    ap.add_argument("--port", type=int, default=SERVER_PORT_DEFAULT)
    ap.add_argument("--host", default="127.0.0.1",
                    help="loopback-only por defecto (local-first)")
    args = ap.parse_args()

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    log(f"http://{args.host}:{args.port}  (Ctrl+C para detener)")
    log(f"repo: {REPO_ROOT}")
    if opencode_installed():
        log(f"opencode: {opencode_installed()} (serve se arranca on-demand vía /api/opencode/ensure)")
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

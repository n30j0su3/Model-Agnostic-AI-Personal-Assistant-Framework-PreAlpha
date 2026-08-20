#!/usr/bin/env python3
"""
v0.4.1-beta: Seleccionar modelo free disponible desde opencode serve.

v0.4.1-beta (fix bug N30 2026-08-19): la detección ahora es AUTH-AWARE.
Antes: se listaban modelos free del catálogo sin verificar credenciales →
en una máquina con opencode instalado y creds configuradas, el framework
"detectaba" credenciales pero luego NO las usaba (el chat servía con el
default global de opencode, no con el modelo asignado). Detectar != usar.

Cambios v0.4.1-beta:
  - Cada modelo listado muestra su estado de credenciales (oc_auth.py):
      [env]       variable de entorno seteada → utilizable
      [auth.json] credencial de `opencode auth login` → utilizable
      [anon]      tier free anónimo (opencode/*-free) → utilizable
      [sin-creds] proveedor detectado pero SIN credenciales → requiere login
  - Orden: autenticados primero; sin-creds al final (no se ocultan: se explica).
  - --auto prefiere el primer modelo AUTENTICADO; si ninguno lo está,
    dice exactamente qué falta y cómo resolverlo (no falla en silencio).

Flujo: descubre puerto del serve (o lo arranca) → consulta
/config/providers → filtra modelos gratuitos (cost 0 / sufijo -free)
→ verifica estado de credenciales → guarda en .opencode/config.json.

Uso interactivo:
    python core/scripts/select_free_model.py

Uso no interactivo (primer modelo free AUTENTICADO):
    python core/scripts/select_free_model.py --auto
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONFIG_PATH = REPO_ROOT / ".opencode" / "config.json"
PORTS = [47017, 47018, 47019, 47020, 47021]

sys.path.insert(0, str(SCRIPT_DIR))
import oc_auth  # noqa: E402  (misma carpeta; stdlib-only)

AUTH_RANK = {"authed_env": 0, "authed_file": 1, "anon": 2, "missing": 3}


def find_serve_port():
    """Retorna el puerto con un serve vivo que responde /config/providers, o None."""
    for port in PORTS:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                if _is_real_serve(port):
                    return port
    return None


def _is_real_serve(port):
    """Verifica que el puerto responda como opencode serve (no otro servicio)."""
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/config/providers",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=4) as r:
            return r.status == 200
    except Exception:
        return False


def find_opencode_exe():
    """Resuelve el ejecutable de opencode (PATH → ~/.opencode/bin)."""
    exe = shutil.which("opencode")
    if exe:
        return exe
    home_bin = Path.home() / ".opencode" / "bin"
    for name in ("opencode", "opencode.exe", "opencode.cmd"):
        cand = home_bin / name
        if cand.exists():
            return str(cand)
    return None


def ensure_opencode_serve():
    """Iniciar opencode serve si no está corriendo. Retorna puerto o None."""
    port = find_serve_port()
    if port:
        print(f"opencode serve detectado en puerto {port}")
        return port

    print("Iniciando opencode serve...")
    exe = find_opencode_exe()
    if not exe:
        print("[ERROR] opencode no está instalado (npm install -g opencode-ai)")
        return None

    try:
        subprocess.Popen(
            [exe, "serve", "--port", "47017", "--hostname", "127.0.0.1"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
    except Exception as e:
        print(f"[ERROR] No se pudo iniciar opencode serve: {e}")
        return None

    for _ in range(20):
        time.sleep(1)
        port = find_serve_port()
        if port:
            print(f"✓ opencode serve iniciado en puerto {port}")
            return port
    print("[ERROR] opencode serve no arrancó en 20s")
    return None


def get_free_models(port, timeout=15):
    """Consultar /config/providers y extraer modelos free CON estado de auth.

    Retorna lista de dicts {id, provider, model, status} ordenada:
    authed_env → authed_file → anon → missing.
    """
    return _get_models(port, timeout=timeout, free_only=True)


def get_usable_models(port, timeout=15):
    """v0.4.1-beta (feedback N30): TODOS los modelos utilizables, sin bloquear.

    Lista el catálogo COMPLETO de proveedores con credenciales (free y paid
    — ej. minimax configurado en otra máquina) + modelos free del resto.
    Nada se oculta ni se bloquea: los sin-creds van al final con su badge,
    porque la facilidad para el usuario manda. Detectar != usar, pero
    TENER credenciales sí debe implicar poder elegir cualquiera de esos
    modelos y que funcione en la sesión.
    """
    return _get_models(port, timeout=timeout, free_only=False)


def _get_models(port, timeout=15, free_only=True):
    """Núcleo compartido del listado de modelos (auth-aware)."""
    url = f"http://127.0.0.1:{port}/config/providers"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return []

    if not isinstance(data, dict):
        return []
    out = []
    auth_data = oc_auth.load_auth_json()
    for p in data.get("providers", []):
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "")
        status = oc_auth.provider_auth_status(p, auth_data)
        has_creds = status in ("authed_env", "authed_file", "anon")
        models = p.get("models", {})
        items = models.items() if isinstance(models, dict) else (
            [(m.get("id", ""), m) for m in models if isinstance(m, dict)]
        )
        for mid, m in items:
            if not isinstance(m, dict):
                continue
            cost = m.get("cost", {}) or {}
            is_free = (
                (cost.get("input") == 0 and cost.get("output") == 0)
                or "free" in str(mid).lower()
            )
            # free_only: solo free (compat). Si no: TODO el catálogo del
            # proveedor con creds (free + paid) y solo free del resto.
            if free_only and not is_free:
                continue
            if not free_only and not is_free and not has_creds:
                continue  # paid sin creds no es ejecutable: free sí, paid no
            out.append({
                "id": f"{pid}/{mid}",
                "provider": pid,
                "model": mid,
                "status": status,
                "free": is_free,
            })
    return sorted(out, key=lambda x: (AUTH_RANK.get(x["status"], 9), x["id"]))


def save_selection(model_id):
    """Guardar modelo seleccionado en .opencode/config.json."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    cfg["model"] = model_id
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"✓ Config actualizado: model = {model_id}")


def verify_model(model_id: str, port=None) -> int:
    """v0.4.1-beta: ping REAL de un modelo específico. Imprime VERIFY_OK si
    respondió (modelo existe + credencial funciona), o la causa exacta.
    Exit codes: 0 ok, 2 sin serve, 3 modelo no está en el catálogo,
    4 credencial/llamada falló. Usado por pa.py --preflight y por el
    botón "Probar modelo" del dashboard."""
    port = port or find_serve_port() or ensure_opencode_serve()
    if port is None:
        print("NO_SERVE")
        return 2

    catalog = get_usable_models(port)
    entry = next((m for m in catalog if m["id"] == model_id), None)
    if entry is None:
        # ¿está en el catálogo pero sin creds?
        raw = _raw_provider_catalog(port)
        in_catalog = any(
            f"{p.get('id','')}/{mid}" == model_id
            for p in raw for mid in (p.get("models") or {})
        )
        if in_catalog:
            print(f"NO_CREDS: {model_id} existe pero su proveedor no tiene credenciales")
        else:
            print(f"NOT_IN_CATALOG: {model_id} no existe en el catálogo local")
        return 3

    ok, detail = _ping_model(port, entry)
    if ok:
        print(f"VERIFY_OK: {model_id} respondió ({detail})")
        return 0
    print(f"PING_FAILED: {model_id} — {detail}")
    return 4


def _raw_provider_catalog(port):
    """Catálogo crudo /config/providers (sin filtrar)."""
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/config/providers",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode()).get("providers", [])
    except Exception:
        return []


def _ping_model(port, entry: dict):
    """Ping real del modelo (mismo patrón que el bridge del dashboard):
    POST /session (título test) → POST /session/{id}/message con model
    objeto → info.modelID presente en la respuesta = credencial FUNCIONA.
    Verificado contra opencode serve 1.4.6."""
    pid, _, mid = entry["id"].partition("/")
    model_obj = {"providerID": pid, "modelID": mid}
    base = f"http://127.0.0.1:{port}"
    try:
        def _req(path, method="POST", body=None):
            data = json.dumps(body).encode() if body is not None else None
            rq = urllib.request.Request(
                base + path, method=method, data=data,
                headers={"Content-Type": "application/json"},
            )
            return urllib.request.urlopen(rq, timeout=60)

        # 1) crear sesión de test
        with _req("/session", body={"title": "PA model test"}) as r:
            raw = r.read().decode()
        sid = None
        try:
            data = json.loads(raw)
            sid = (data[0] if isinstance(data, list) and data else {}).get("id") \
                if not isinstance(data, dict) else data.get("id")
        except Exception:
            # serve puede devolver event-stream: buscar "id" con regex
            import re as _re
            m = _re.search(r'"id"\s*:\s*"([^"]+)"', raw)
            sid = m.group(1) if m else None
        if not sid:
            return False, "no se pudo crear sesión"

        # 2) mensaje con el modelo objeto
        with _req(f"/session/{sid}/message", body={
            "model": model_obj,
            "parts": [{"type": "text", "text": "ping"}],
        }) as r:
            events = r.read().decode()

        # 3) verificar: si la respuesta trae providerID+modelID del modelo
        #    pedido, la credencial funcionó. Calibrado contra respuesta real
        #    de serve 1.4.6 (modelID aparece ANTES que providerID, sin espacios)
        import re as _re
        got_mid = _re.search(r'"modelID"\s*:\s*"' + _re.escape(mid) + '"', events)
        got_pid = _re.search(r'"providerID"\s*:\s*"' + _re.escape(pid) + '"', events)
        if got_mid and got_pid:
            return True, "respondió con el modelo pedido"
        # error del proveedor → extraer mensaje
        m_err = _re.search(r'"message"\s*:\s*"([^"]{0,140})', events)
        if m_err:
            return False, m_err.group(1)
        return False, "la respuesta no confirmó el modelo (posible fallback silencioso)"
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode()[:140]
        except Exception:
            pass
        return False, f"HTTP {e.code} {detail}".strip()
    except Exception as e:
        return False, str(e)[:140]


def main():
    ap = argparse.ArgumentParser(
        description="Seleccionar modelo de opencode (auth-aware, sin bloqueos)")
    ap.add_argument(
        "--auto", action="store_true",
        help="Seleccionar automáticamente el primer modelo AUTENTICADO")
    ap.add_argument(
        "--verify", metavar="MODEL",
        help="Ping real de un modelo (imprime VERIFY_OK o la causa)")
    ap.add_argument(
        "--all", action="store_true",
        help="Listar TODOS los modelos utilizables (catálogo completo de "
             "proveedores con creds + free), no solo free")
    args = ap.parse_args()

    if args.verify:
        return verify_model(args.verify)

    port = ensure_opencode_serve()
    if port is None:
        print("NO_SERVE")
        return 1

    models = get_usable_models(port) if args.all else get_free_models(port)
    if not models:
        print("NO_MODELS")
        return 1

    label = "utilizables (con credenciales + free)" if args.all else "free"
    print(f"Modelos {label} disponibles (con credenciales primero):")
    for i, m in enumerate(models, 1):
        badge = oc_auth.provider_auth_badge(m["status"])
        marker = "✓" if m["status"] != "missing" else "⚠"
        free_tag = "" if m.get("free", True) else " (paid)"
        print(f"  {i}. {m['id']}  [{badge}] {marker}{free_tag}")

    if args.auto:
        authed = [m for m in models if m["status"] != "missing"]
        if not authed:
            print("\n[!] Ningún modelo free tiene credenciales en esta máquina.")
            print("    Cómo habilitar:")
            print("      opencode auth login   → login interactivo del proveedor")
            print("      (o exporta la variable de entorno que pide el proveedor)")
            return 2
        selected = authed[0]
    else:
        try:
            raw = input("\nSelecciona un número (Enter = 1): ").strip()
            idx = int(raw) - 1 if raw else 0
            if not (0 <= idx < len(models)):
                print("[ERROR] Selección fuera de rango")
                return 1
            selected = models[idx]
        except (ValueError, EOFError):
            selected = models[0]

    print(f"\nSeleccionado: {selected['id']}")
    save_selection(selected["id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
    url = f"http://127.0.0.1:{port}/config/providers"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return []

    if not isinstance(data, dict):
        return []
    free = []
    auth_data = oc_auth.load_auth_json()
    for p in data.get("providers", []):
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "")
        status = oc_auth.provider_auth_status(p, auth_data)
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
            if is_free:
                free.append({
                    "id": f"{pid}/{mid}",
                    "provider": pid,
                    "model": mid,
                    "status": status,
                })
    return sorted(free, key=lambda x: (AUTH_RANK.get(x["status"], 9), x["id"]))


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


def main():
    ap = argparse.ArgumentParser(
        description="Seleccionar modelo free de opencode (auth-aware)")
    ap.add_argument(
        "--auto", action="store_true",
        help="Seleccionar automáticamente el primer modelo free AUTENTICADO")
    args = ap.parse_args()

    port = ensure_opencode_serve()
    if port is None:
        print("NO_SERVE")
        return 1

    models = get_free_models(port, timeout=15)
    if not models:
        print("NO_MODELS")
        return 1

    print("Modelos free disponibles (con credenciales primero):")
    for i, m in enumerate(models, 1):
        badge = oc_auth.provider_auth_badge(m["status"])
        marker = "✓" if m["status"] != "missing" else "⚠"
        print(f"  {i}. {m['id']}  [{badge}] {marker}")

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

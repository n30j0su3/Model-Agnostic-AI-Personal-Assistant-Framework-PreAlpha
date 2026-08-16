#!/usr/bin/env python3
"""
v0.4.0-beta: Seleccionar modelo free disponible desde opencode serve.

Descubre el puerto del serve (o lo arranca), consulta
/config/providers, filtra modelos gratuitos (cost 0 / sufijo -free)
y guarda la selección en .opencode/config.json.

Uso interactivo:
    python core/scripts/select_free_model.py

Uso no interactivo (primer modelo free):
    python core/scripts/select_free_model.py --auto
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / ".opencode" / "config.json"
PORTS = [47017, 47018, 47019, 47020, 47021]


def find_serve_port():
    """Retorna el puerto con un serve vivo, o None."""
    for port in PORTS:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return port
    return None


def ensure_opencode_serve():
    """Iniciar opencode serve si no está corriendo. Retorna puerto o None."""
    port = find_serve_port()
    if port:
        print(f"opencode serve detectado en puerto {port}")
        return port

    print("Iniciando opencode serve...")
    import shutil
    exe = shutil.which("opencode")
    if not exe:
        home_bin = Path.home() / ".opencode" / "bin"
        for name in ("opencode", "opencode.exe", "opencode.cmd"):
            cand = home_bin / name
            if cand.exists():
                exe = str(cand)
                break
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

    for _ in range(12):
        time.sleep(1)
        port = find_serve_port()
        if port:
            print(f"✓ opencode serve iniciado en puerto {port}")
            return port
    print("[ERROR] opencode serve no arrancó en 12s")
    return None


def get_free_models(port, timeout=15):
    """Consultar /config/providers y extraer modelos free."""
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
    for p in data.get("providers", []):
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "")
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
                free.append(f"{pid}/{mid}")
    return sorted(set(free))


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
    ap = argparse.ArgumentParser(description="Seleccionar modelo free de opencode")
    ap.add_argument("--auto", action="store_true",
                    help="Seleccionar automáticamente el primer modelo free")
    args = ap.parse_args()

    port = ensure_opencode_serve()
    if port is None:
        print("NO_SERVE")
        return 1

    models = get_free_models(port, timeout=15)
    if not models:
        print("NO_MODELS")
        return 1

    print("Modelos free disponibles:")
    for i, m in enumerate(models, 1):
        print(f"  {i}. {m}")

    if args.auto:
        selected = models[0]
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

    print(f"\nSeleccionado: {selected}")
    save_selection(selected)
    return 0


if __name__ == "__main__":
    sys.exit(main())

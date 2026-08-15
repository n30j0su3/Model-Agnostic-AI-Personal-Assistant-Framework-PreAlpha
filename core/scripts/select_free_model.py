#!/usr/bin/env python3
"""v0.5.0-alpha: Seleccionar modelo free disponible desde opencode serve."""
import subprocess, json, urllib.request, socket, sys, time, os, re


def ensure_opencode_serve():
    """Iniciar opencode serve si no está corriendo."""
    import socket, subprocess, time, shutil
    
    # Verificar si ya hay un serve corriendo
    for port in range(47017, 47022):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                s.close()
                print(f"opencode serve detectado en puerto {port}")
                return port
            s.close()
        except:
            pass
    
    # No hay serve, intentar iniciar
    print("Iniciando opencode serve...")
    exe = shutil.which("opencode")
    if not exe:
        home_bin = Path.home() / ".opencode" / "bin" / "opencode"
        if home_bin.exists():
            exe = str(home_bin)
    
    if not exe:
        return None
    
    try:
        # Iniciar en background
        proc = subprocess.Popen(
            [exe, "serve", "--port", "47017"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)  # esperar arranque
        
        # Verificar si arrancó
        for _ in range(10):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if s.connect_ex(('127.0.0.1', 47017)) == 0:
                    s.close()
                    print(f"✓ opencode serve iniciado en puerto 47017")
                    return 47017
                s.close()
            except:
                pass
            time.sleep(1)
    except Exception as e:
        print(f"Error iniciando serve: {e}")
    
    return None

def get_free_models(timeout=10):
    """Consultar /config de opencode serve y extraer modelos free."""
    for port in [47017, 47018, 47019, 47020, 47021]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex(('127.0.0.1', port))
            s.close()
            if result == 0:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/config", timeout=timeout) as r:
                        cfg = json.loads(r.read().decode())
                        providers = cfg.get("providers", [])
                        free = []
                        for p in providers:
                            if isinstance(p, dict):
                                name = p.get("name", p.get("id", ""))
                                for m in p.get("models", []):
                                    if isinstance(m, dict):
                                        mid = m.get("id", "")
                                        if m.get("free", False) or "free" in mid.lower():
                                            free.append(f"{name}/{mid}" if name else mid)
                        return free
                except:
                    pass
        except:
            pass
    return []

def main():
    port = ensure_opencode_serve()
    if port is None:
        print('NO_SERVE')
        return 1
    models = get_free_models(timeout=15)
    if not models:
        print("NO_MODELS")
        return 1
    
    print("Modelos free disponibles:")
    for i, m in enumerate(models, 1):
        print(f"  {i}. {m}")
    
    selected = models[0]
    print(f"\nSeleccionado: {selected}")
    
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".opencode", "config.json")
    try:
        with open(cfg_path, "r") as f:
            cfg = json.load(f)
        cfg["model"] = selected
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=2)
        print(f"✓ Config actualizado: model = {selected}")
    except Exception as e:
        print(f"✗ Error guardando config: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())

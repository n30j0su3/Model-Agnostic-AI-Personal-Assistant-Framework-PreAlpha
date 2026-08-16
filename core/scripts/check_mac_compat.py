#!/usr/bin/env python3
"""v0.4.0-beta: Verificar compatibilidad macOS y ajustar paths."""
import sys, os, platform, subprocess
from pathlib import Path

def check_mac():
    if platform.system() != "Darwin":
        print("Esto no es macOS. Saliendo.")
        return 1
    
    print("=== Verificación de compatibilidad macOS ===")
    print(f"macOS {platform.mac_ver()[0]} ({platform.machine()})")
    
    # Python
    py = sys.executable
    print(f"\nPython: {py}")
    r = subprocess.run([py, "--version"], capture_output=True, text=True)
    print(f"  {r.stdout.strip()}")
    
    # opencode
    oc = subprocess.run(["which", "opencode"], capture_output=True, text=True)
    if oc.stdout.strip():
        print(f"\nopencode: {oc.stdout.strip()}")
        r = subprocess.run(["opencode", "--version"], capture_output=True, text=True)
        print(f"  {r.stdout.strip()}")
    else:
        print("\nopencode: NO encontrado")
        print("  Instalar: brew install opencode  O  npm install -g opencode-ai")
    
    # npm
    npm = subprocess.run(["which", "npm"], capture_output=True, text=True)
    if npm.stdout.strip():
        print(f"\nnpm: {npm.stdout.strip()}")
    else:
        print("\nnpm: NO encontrado (requerido para opencode)")
    
    # brew
    brew = subprocess.run(["which", "brew"], capture_output=True, text=True)
    if brew.stdout.strip():
        print(f"\nHomebrew: {brew.stdout.strip()}")
    else:
        print("\nHomebrew: NO encontrado (recomendado)")
    
    # paths específicos de macOS
    print("\n=== Paths críticos ===")
    home = Path.home()
    dirs = [
        home / ".opencode",
        home / "Library" / "Application Support" / "opencode",
        home / ".nvm",
        Path("/opt/homebrew/bin"),
        Path("/usr/local/bin")
    ]
    for d in dirs:
        exists = "✓" if d.exists() else "✗"
        print(f"  {exists} {d}")
    
    print("\n=== Verificación completada ===")
    return 0

if __name__ == "__main__":
    sys.exit(check_mac())

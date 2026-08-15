#!/usr/bin/env python3
"""
FreakingJSON PA Framework — Dashboard Launcher (v0.5.0-alpha)

Launcher inteligente para usuarios no-tech:
- Detecta SO (Windows/macOS/Linux)
- Verifica dependencias (Python, opencode)
- Inicia opencode serve si es necesario
- Abre dashboard en browser automáticamente
- Todo en un solo click/doble-click

Uso:
  Windows: doble-click en "dashboard-launcher.bat"
  macOS:   doble-click en "dashboard-launcher.command"
  Linux:   ./dashboard-launcher.sh
"""

import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # core/scripts → core → root
DASHBOARD_HTML = REPO_ROOT / "dashboard.html"
SERVER_SCRIPT = REPO_ROOT / "core" / "scripts" / "dashboard_server.py"
OPENCODE_PORT = 47017
DASHBOARD_PORT = 8760

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log(msg, color=Colors.RESET, bold=False):
    prefix = f"{Colors.BOLD}{color}" if bold else color
    print(f"{prefix}[PA Dashboard] {msg}{Colors.RESET}", flush=True)

def check_python():
    """Verificar Python 3.10+."""
    log("Verificando Python...", Colors.CYAN)
    py = sys.executable
    try:
        result = subprocess.run([py, "--version"], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip()
        log(f"✓ {version}", Colors.GREEN)
        
        # Extraer versión mayor
        import re
        m = re.search(r'Python (\d+)\.(\d+)', version, re.I)
        if m:
            major, minor = int(m.group(1)), int(m.group(2))
            if major < 3 or (major == 3 and minor < 10):
                log(f"✗ Python 3.10+ requerido (tienes {major}.{minor})", Colors.RED, bold=True)
                return False
        return True
    except Exception as e:
        log(f"✗ Error verificando Python: {e}", Colors.RED, bold=True)
        return False

def check_opencode():
    """Verificar opencode instalado."""
    log("Verificando opencode...", Colors.CYAN)
    
    exe = shutil.which("opencode")
    if exe:
        log(f"✓ opencode detectado: {exe}", Colors.GREEN)
        return exe
    
    # Fallback: ~/.opencode/bin
    home_bin = Path.home() / ".opencode" / "bin"
    for name in ["opencode", "opencode.exe", "opencode.cmd"]:
        cand = home_bin / name
        if cand.exists():
            log(f"✓ opencode detectado: {cand}", Colors.GREEN)
            return str(cand)
    
    log("✗ opencode no detectado", Colors.RED, bold=True)
    log("Instala con: npm install -g opencode-ai", Colors.YELLOW)
    return None

def is_port_in_use(port):
    """Verificar si un puerto está en uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_opencode_serve(opencode_exe):
    """Iniciar opencode serve en background."""
    if is_port_in_use(OPENCODE_PORT):
        log(f"opencode serve ya corriendo en puerto {OPENCODE_PORT}", Colors.GREEN)
        return True
    
    log("Iniciando opencode serve...", Colors.CYAN)
    
    try:
        proc = subprocess.Popen(
            [opencode_exe, "serve", "--port", str(OPENCODE_PORT)],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        # Esperar arranque
        for i in range(15):
            time.sleep(1)
            if is_port_in_use(OPENCODE_PORT):
                log(f"✓ opencode serve iniciado en puerto {OPENCODE_PORT}", Colors.GREEN, bold=True)
                return True
        
        log("✗ opencode serve no arrancó en 15s", Colors.RED, bold=True)
        return False
    except Exception as e:
        log(f"✗ Error iniciando opencode serve: {e}", Colors.RED, bold=True)
        return False

def start_dashboard_server():
    """Iniciar dashboard server."""
    if is_port_in_use(DASHBOARD_PORT):
        log(f"Dashboard server ya corriendo en puerto {DASHBOARD_PORT}", Colors.GREEN)
        return True
    
    log("Iniciando dashboard server...", Colors.CYAN)
    
    if not SERVER_SCRIPT.exists():
        log(f"✗ No encontrado: {SERVER_SCRIPT}", Colors.RED, bold=True)
        return False
    
    try:
        proc = subprocess.Popen(
            [sys.executable, str(SERVER_SCRIPT), "--port", str(DASHBOARD_PORT)],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        # Esperar arranque
        for i in range(10):
            time.sleep(1)
            if is_port_in_use(DASHBOARD_PORT):
                log(f"✓ Dashboard server iniciado en puerto {DASHBOARD_PORT}", Colors.GREEN, bold=True)
                return True
        
        log("✗ Dashboard server no arrancó en 10s", Colors.RED, bold=True)
        return False
    except Exception as e:
        log(f"✗ Error iniciando dashboard server: {e}", Colors.RED, bold=True)
        return False

def open_dashboard():
    """Abrir dashboard en browser."""
    url = f"http://127.0.0.1:{DASHBOARD_PORT}"
    log(f"Abriendo dashboard en {url}...", Colors.CYAN)
    
    try:
        webbrowser.open(url)
        log("✓ Dashboard abierto en tu navegador", Colors.GREEN, bold=True)
        return True
    except Exception as e:
        log(f"✗ Error abriendo browser: {e}", Colors.RED)
        return False

def show_instructions():
    """Mostrar instrucciones para el usuario."""
    print()
    log("=" * 60, Colors.CYAN, bold=True)
    log("Dashboard listo para usar", Colors.GREEN, bold=True)
    log("=" * 60, Colors.CYAN)
    print()
    log("🌐 Dashboard: http://127.0.0.1:8760", Colors.CYAN)
    log("💡 Tip: Mantén esta ventana abierta mientras usas el dashboard", Colors.YELLOW)
    print()
    log("Características:", Colors.BOLD)
    log("  • Chat con IA vía opencode", Colors.CYAN)
    log("  • Gestión de sesiones", Colors.CYAN)
    log("  • Selección de modelos free", Colors.CYAN)
    log("  • Configuración MASTER.md/profile.md", Colors.CYAN)
    log("  • 100% local, sin cloud", Colors.GREEN)
    print()
    log("Presiona Ctrl+C para cerrar", Colors.DIM)
    print()

def main():
    """Main del launcher."""
    print()
    log("=" * 60, Colors.CYAN, bold=True)
    log("FreakingJSON PA Framework — Dashboard Launcher", Colors.BOLD)
    log(f"v0.5.0-alpha | {platform.system()} {platform.release()} ({platform.machine()})", Colors.DIM)
    log("=" * 60, Colors.CYAN)
    print()
    
    # 1) Verificar Python
    if not check_python():
        input("Presiona Enter para salir...")
        return 1
    
    # 2) Verificar opencode
    opencode_exe = check_opencode()
    if not opencode_exe:
        log("\n¿Quieres instalar opencode ahora?", Colors.YELLOW)
        log("  npm install -g opencode-ai", Colors.DIM)
        input("\nPresiona Enter después de instalar...")
    
    # 3) Iniciar opencode serve
    if not start_opencode_serve(opencode_exe):
        log("Continuando sin opencode serve (algunas funciones no estarán disponibles)", Colors.YELLOW)
    
    # 4) Iniciar dashboard server
    if not start_dashboard_server():
        log("Intentando abrir dashboard.html directamente...", Colors.YELLOW)
        if DASHBOARD_HTML.exists():
            webbrowser.open(f"file://{DASHBOARD_HTML}")
            input("Presiona Enter para salir...")
            return 0
        else:
            log(f"✗ No encontrado: {DASHBOARD_HTML}", Colors.RED, bold=True)
            return 1
    
    # 5) Abrir dashboard
    if not open_dashboard():
        return 1
    
    # 6) Mostrar instrucciones y mantener vivo
    show_instructions()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("\nCerrando dashboard...", Colors.CYAN)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

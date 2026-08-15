#!/bin/bash
# FreakingJSON PA Framework — Dashboard Launcher (macOS/Linux)
# Doble-click para iniciar el dashboard con auto-configuración

echo ""
echo "==============================================="
echo "  FreakingJSON PA Framework"
echo "  Dashboard Launcher v0.5.0-alpha"
echo "==============================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no detectado."
    echo "Instala Python 3.10+ (macOS: brew install python3)"
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Verificar opencode
if ! command -v opencode &> /dev/null; then
    if [ -f "$HOME/.opencode/bin/opencode" ]; then
        export PATH="$HOME/.opencode/bin:$PATH"
    else
        echo "[WARNING] opencode no detectado."
        echo "Para usar chat con IA, instala: npm install -g opencode-ai"
        echo ""
        read -p "¿Quieres instalar opencode ahora? (Y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Instalando opencode..."
            npm install -g opencode-ai
        fi
    fi
fi

# Iniciar launcher
echo "Iniciando dashboard..."
python3 "$(dirname "$0")/core/scripts/dashboard_launcher.py"

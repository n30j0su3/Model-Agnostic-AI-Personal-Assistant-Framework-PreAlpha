#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Detect Python
PY_CMD=""
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
fi

if [ -z "$PY_CMD" ]; then
    echo "[ERROR] Python no encontrado. Es obligatorio."
    echo "[INFO] Instala Python 3.11+: https://www.python.org/downloads/"
    exit 1
fi

# Auto-install if profile missing
if [ ! -f "core/.context/profile.md" ]; then
    echo "[INFO] Primera ejecución detectada. Iniciando instalador..."
    $PY_CMD core/scripts/install.py
    if [ $? -ne 0 ]; then
        echo "[ERROR] Instalación incompleta."
        exit 1
    fi
fi

# Delegate to main Python script
$PY_CMD core/scripts/pa.py "$@"
#!/bin/bash
# FreakingJSON PA Framework — Dashboard Launcher (macOS)
# Doble-click para iniciar el dashboard con auto-configuración

osascript -e 'tell app "Terminal" to do script "cd '"$(dirname "$0")"' && ./dashboard-launcher.sh"'

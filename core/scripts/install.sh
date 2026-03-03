#!/bin/bash
#
# Instalador Pre-Alpha simplificado para macOS/Linux
# Crea estructura, configura perfil y sincroniza contexto.
#

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Directorios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$CORE_DIR")"
CONTEXT_DIR="$CORE_DIR/.context"

# Comandos de CLI
CLI_COMMANDS=("opencode" "claude" "gemini" "codex")
LOCAL_CLI_COMMANDS=("ollama" "lms")

print_ok() {
    echo -e "${GREEN}  [OK] $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}  [WARN] $1${NC}"
}

print_error() {
    echo -e "${RED}  [ERROR] $1${NC}"
}

print_info() {
    echo -e "${CYAN}  [INFO] $1${NC}"
}

prompt_yes_no() {
    local msg="$1"
    local default="${2:-n}"
    local suffix="[s/N]"
    [[ "$default" == "y" ]] && suffix="[S/n]"
    
    read -p "  $msg $suffix: " choice
    choice=${choice:-$default}
    [[ "$choice" =~ ^[SsYy]$ ]]
}

# Header
echo -e "\n${BOLD}${CYAN}  Personal Assistant Framework — Instalador Pre-Alpha (macOS/Linux)${NC}\n"

# Detectar sistema
OS_NAME=$(uname -s)
OS_VERSION=$(uname -r)
print_info "Sistema: $OS_NAME $OS_VERSION"

# Verificar Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_info "Python: $PYTHON_VERSION"
else
    print_error "Python 3.11+ requerido. Instala desde https://python.org/downloads/"
    exit 1
fi

print_info "Directorio: $REPO_ROOT"
echo ""

# Crear estructura de directorios
dirs=(
    "$CONTEXT_DIR"
    "$CONTEXT_DIR/sessions"
    "$CONTEXT_DIR/codebase"
    "$CONTEXT_DIR/backups"
    "$CORE_DIR/agents/subagents"
    "$CORE_DIR/skills/core"
    "$REPO_ROOT/workspaces"
    "$REPO_ROOT/docs"
    "$REPO_ROOT/config"
)

for dir in "${dirs[@]}"; do
    mkdir -p "$dir"
done
print_ok "Estructura de directorios verificada."

# Verificar MASTER.md
MASTER_FILE="$CONTEXT_DIR/MASTER.md"
TEMPLATE_FILE="$CONTEXT_DIR/MASTER.template.md"

if [[ ! -f "$MASTER_FILE" ]]; then
    if [[ -f "$TEMPLATE_FILE" ]]; then
        cp "$TEMPLATE_FILE" "$MASTER_FILE"
        print_ok "MASTER.md restaurado desde template."
    else
        print_warn "MASTER.md no encontrado y sin template disponible."
    fi
fi

# Detectar CLIs instalados
found=()
for cli in "${CLI_COMMANDS[@]}" "${LOCAL_CLI_COMMANDS[@]}"; do
    if command -v "$cli" &> /dev/null; then
        found+=("$cli")
    fi
done

if [[ ${#found[@]} -gt 0 ]]; then
    print_ok "CLIs detectados: ${found[*]}"
else
    print_warn "Ningún CLI de IA detectado. Instala: opencode, claude, gemini, o codex"
    print_info "Para instalar OpenCode: npm install -g opencode-ai"
fi

# Seleccionar CLI por defecto
default_cli="opencode"
if [[ ${#found[@]} -gt 0 ]]; then
    echo ""
    echo "  Selecciona CLI por defecto:"
    for i in "${!found[@]}"; do
        idx=$((i + 1))
        echo "    $idx. ${found[$i]}"
    done
    read -p "  Selección [1]: " choice
    choice=${choice:-1}
    
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#found[@]} )); then
        default_cli="${found[$((choice - 1))]}"
    elif [[ ${#found[@]} -gt 0 ]]; then
        default_cli="${found[0]}"
    fi
fi

# Guardar perfil
VERSION="0.1.0-alpha"
VERSION_FILE="$REPO_ROOT/VERSION"
if [[ -f "$VERSION_FILE" ]]; then
    VERSION=$(cat "$VERSION_FILE" | tr -d '\n')
fi

DATE_STR=$(date +%Y-%m-%d)
PROFILE_FILE="$CONTEXT_DIR/profile.md"

cat > "$PROFILE_FILE" << EOF
# Perfil de Instalación

- **Framework Version**: $VERSION
- **Fecha**: $DATE_STR
- **CLI default**: $default_cli
- **Sistema Operativo**: $OS_NAME $OS_VERSION
EOF

print_ok "Perfil guardado."

# Sincronizar contexto (si existe el script)
SYNC_SCRIPT="$SCRIPT_DIR/sync-context.py"
if [[ -f "$SYNC_SCRIPT" ]]; then
    print_info "Sincronizando contexto..."
    python3 "$SYNC_SCRIPT" || print_warn "Sincronización completada con advertencias"
fi

# Done
echo ""
echo -e "${GREEN}${BOLD}  ==================================================${NC}"
echo -e "${GREEN}${BOLD}  [OK] Instalación completada.${NC}"
echo -e "${GREEN}${BOLD}  ==================================================${NC}"
echo ""
echo -e "${CYAN}  Siguiente paso: ejecuta ./pa.sh para iniciar el framework.${NC}"
echo ""

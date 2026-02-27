#!/bin/bash
#
# Sincronización BASE → DEV
# Trae mejoras del framework puro al entorno de desarrollo
#
# Uso: ./sync-base-to-dev.sh [--dry-run]

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
BASE_PATH="${BASE_PATH:-C:/ACTUAL/FreakingJSON-pa/Model-Agnostic-AI-Personal-Assistant-Framework}"
DEV_PATH="${DEV_PATH:-C:/ACTUAL/FreakingJSON-pa/Pa_Pre_alpha_Opus_4_6_DEV}"

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

DRY_RUN=false

verify_directories() {
    log_info "Verificando directorios..."
    
    if [ ! -d "$DEV_PATH" ]; then
        log_error "Directorio DEV no encontrado: $DEV_PATH"
        exit 1
    fi
    
    log_success "Directorios verificados"
}

setup_remote() {
    log_info "Configurando remote BASE..."
    
    cd "$DEV_PATH"
    
    if ! git remote | grep -q "^BASE$"; then
        git remote add BASE "https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework.git"
        log_success "Remote BASE agregado"
    else
        log_info "Remote BASE ya existe"
    fi
}

fetch_and_merge() {
    log_info "Trayendo cambios de BASE..."
    
    cd "$DEV_PATH"
    
    # Fetch
    git fetch BASE main --quiet
    
    # Mostrar commits que se traerán
    log_info "Commits a sincronizar:"
    git log HEAD..BASE/main --oneline || true
    
    local commit_count=$(git rev-list --count HEAD..BASE/main 2>/dev/null || echo "0")
    
    if [ "$commit_count" -eq "0" ]; then
        log_success "DEV ya está actualizado con BASE"
        return 0
    fi
    
    log_info "Total de commits nuevos: $commit_count"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "[DRY RUN] No se aplicarán cambios"
        log_info "Comando que se ejecutaría: git merge BASE/main --no-commit"
        return 0
    fi
    
    # Confirmación
    read -p "¿Aplicar estos cambios a DEV? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log_info "Cancelado"
        return 0
    fi
    
    # Merge sin commit para revisar
    log_info "Merge de BASE/main..."
    
    if git merge BASE/main --no-commit --no-ff; then
        log_success "Merge exitoso sin conflictos"
    else
        log_warn "Hay conflictos que resolver manualmente"
        log_info "Archivos en conflicto:"
        git diff --name-only --diff-filter=U
        
        read -p "¿Resolverás los conflictos manualmente? (yes/abort): " resolve
        if [[ "$resolve" != "yes" ]]; then
            git merge --abort
            log_info "Merge abortado"
            return 1
        fi
        
        log_info "Por favor resuelve los conflictos y luego ejecuta:"
        log_info "  git commit -m 'Sync: BASE → DEV $(date +%Y-%m-%d)'"
        return 0
    fi
    
    # Verificar que no se sobreescriben datos de usuario
    log_info "Verificando protección de datos de usuario..."
    
    # Archivos que nunca deben cambiar desde BASE
    PROTECTED_FILES=(
        "core/.context/sessions/"
        "core/.context/codebase/"
        "core/.context/MASTER.md"
        "workspaces/"
    )
    
    local has_protected_changes=false
    
    for protected in "${PROTECTED_FILES[@]}"; do
        if git diff --cached --name-only | grep -q "$protected"; then
            log_warn "Cambios detectados en: $protected"
            has_protected_changes=true
        fi
    done
    
    if [ "$has_protected_changes" = true ]; then
        log_warn "⚠️  Se detectaron cambios en archivos protegidos"
        log_info "Revisa los cambios antes de continuar"
        
        read -p "¿Los cambios en archivos protegidos son esperados? (yes/no): " confirm_protected
        if [[ "$confirm_protected" != "yes" ]]; then
            git merge --abort
            log_info "Merge abortado para proteger datos de usuario"
            return 1
        fi
    fi
    
    # Commit
    git commit -m "Sync: BASE → DEV $(date +%Y-%m-%d)

Trae mejoras del framework desde BASE:
$(git log HEAD~1..HEAD --oneline)

Preserva:
- Sesiones de usuario
- Configuraciones locales
- Workspaces y proyectos"
    
    log_success "Sync BASE → DEV completado"
    log_info "Resumen de cambios:"
    git log -1 --stat
}

show_menu() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     SYNC BASE → DEV (Traer mejoras del framework)         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Este script trae mejoras del framework desde BASE a DEV."
    echo ""
    echo "⚠️  Preserva automáticamente:"
    echo "   • Sesiones de usuario (core/.context/sessions/)"
    echo "   • Configuraciones locales (core/.context/MASTER.md)"
    echo "   • Workspaces y proyectos (workspaces/)"
    echo "   • Base de conocimiento (core/.context/codebase/)"
    echo ""
}

main() {
    # Parse args
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                show_menu
                echo "Uso: $0 [--dry-run]"
                exit 0
                ;;
            *)
                log_error "Opción desconocida: $1"
                exit 1
                ;;
        esac
    done
    
    show_menu
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "MODO DRY RUN"
    fi
    
    verify_directories
    setup_remote
    fetch_and_merge
    
    echo ""
    log_success "¡Proceso completado!"
}

main "$@"

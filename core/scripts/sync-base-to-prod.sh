#!/bin/bash
#
# Sincronización BASE → PROD
# Publica versión limpia del framework al repo público
#
# Uso: ./sync-base-to-prod.sh [--dry-run]

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
BASE_PATH="${BASE_PATH:-C:/ACTUAL/FreakingJSON-pa/Model-Agnostic-AI-Personal-Assistant-Framework}"
PROD_PATH="${PROD_PATH:-C:/ACTUAL/FreakingJSON-pa/Pa_Pre_alpha_Opus_4_6}"

# Remote
PROD_REMOTE="https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git"

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

DRY_RUN=false
TEMP_BRANCH=""
SYNC_DATE=$(date +%Y%m%d_%H%M%S)

# Verificar directorios
verify_directories() {
    log_info "Verificando directorios..."
    
    if [ ! -d "$BASE_PATH" ]; then
        log_error "BASE no encontrado: $BASE_PATH"
        exit 1
    fi
    
    log_success "Directorios verificados"
}

# Validar .gitignore en BASE
validate_gitignore() {
    log_info "Validando .gitignore..."
    
    cd "$BASE_PATH"
    
    local required_excludes=(
        "core/.context/sessions/"
        "core/.context/codebase/"
        "core/.context/MASTER.md"
        "workspaces/"
    )
    
    local missing=0
    for exclude in "${required_excludes[@]}"; do
        if ! grep -q "$exclude" .gitignore; then
            log_error "Falta en .gitignore: $exclude"
            missing=$((missing + 1))
        fi
    done
    
    if [ $missing -gt 0 ]; then
        log_error ".gitignore incompleto. No se puede continuar."
        exit 1
    fi
    
    log_success ".gitignore validado"
}

# Validar que no hay archivos sensibles en staging
validate_no_sensitive_files() {
    log_info "Validando que no hay archivos sensibles..."
    
    cd "$BASE_PATH"
    
    # Archivos que NUNCA deben estar
    local forbidden_patterns=(
        "core/.context/sessions/"
        "core/.context/codebase/"
        "core/.context/MASTER.md"
        "workspaces/"
        ".env"
        "api_key"
        "secret"
        "password"
    )
    
    local found=false
    
    for pattern in "${forbidden_patterns[@]}"; do
        if git ls-files | grep -q "$pattern"; then
            log_error "Archivo prohibido encontrado: $pattern"
            found=true
        fi
    done
    
    if [ "$found" = true ]; then
        log_error "Se encontraron archivos sensibles. Abortando."
        exit 1
    fi
    
    log_success "Validación de seguridad pasada"
}

# Crear rama de release
create_release_branch() {
    TEMP_BRANCH="release-${SYNC_DATE}"
    
    log_info "Creando rama de release: $TEMP_BRANCH"
    
    cd "$BASE_PATH"
    git checkout -b "$TEMP_BRANCH"
    
    log_success "Rama creada"
}

# Validación final exhaustiva
final_validation() {
    log_info "Validación final..."
    
    cd "$BASE_PATH"
    
    # 1. No datos de usuario
    if find . -path "./core/.context/sessions" -prune -o -print | grep -q "sessions"; then
        log_error "Directorio sessions/ no debería existir en BASE"
        return 1
    fi
    
    # 2. Solo archivos de framework
    log_info "Archivos a publicar:"
    git ls-files | head -20
    local total_files=$(git ls-files | wc -l)
    log_info "Total: $total_files archivos"
    
    # 3. Sin binarios grandes
    local large_files=$(find . -type f -size +1M 2>/dev/null | wc -l)
    if [ "$large_files" -gt 0 ]; then
        log_warn "Archivos grandes detectados: $large_files"
        find . -type f -size +1M -ls
    fi
    
    log_success "Validación final pasada"
}

# Push a PROD
push_to_prod() {
    if [ "$DRY_RUN" = true ]; then
        log_warn "[DRY RUN] No se hará push"
        log_info "Comando: git push PROD $TEMP_BRANCH:main --force-with-lease"
        return 0
    fi
    
    log_info "Push a PROD..."
    
    cd "$BASE_PATH"
    
    # Configurar remote
    if ! git remote | grep -q "^PROD$"; then
        git remote add PROD "$PROD_REMOTE"
        log_info "Remote PROD agregado"
    fi
    
    # Push con force-with-lease (seguro)
    if git push PROD "$TEMP_BRANCH:main" --force-with-lease; then
        log_success "Push a PROD exitoso"
        log_info "URL: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha"
    else
        log_error "Falló el push a PROD"
        return 1
    fi
}

# Limpiar
cleanup() {
    if [ -n "$TEMP_BRANCH" ]; then
        log_info "Limpiando rama temporal..."
        cd "$BASE_PATH"
        git checkout main 2>/dev/null || true
        git branch -D "$TEMP_BRANCH" 2>/dev/null || true
    fi
}

# Main
main() {
    # Parse args
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                echo "Sincronización BASE → PROD"
                echo ""
                echo "ADVERTENCIA: Esto publica a un repositorio PÚBLICO"
                echo ""
                echo "Uso: $0 [--dry-run]"
                exit 0
                ;;
            *)
                log_error "Opción desconocida: $1"
                exit 1
                ;;
        esac
    done
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     SYNC BASE → PROD (Publicar a repositorio PÚBLICO)     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        log_warn "MODO DRY RUN - No se harán cambios reales"
    else
        log_warn "⚠️  ESTO PUBLICARÁ CÓDIGO A UN REPO PÚBLICO"
        echo ""
        read -p "¿Estás seguro? Escribe 'PUBLICAR' para continuar: " confirm
        if [[ "$confirm" != "PUBLICAR" ]]; then
            log_info "Cancelado"
            exit 0
        fi
    fi
    
    verify_directories
    validate_gitignore
    validate_no_sensitive_files
    create_release_branch
    final_validation
    push_to_prod
    cleanup
    
    echo ""
    log_success "¡Sincronización BASE → PROD completada!"
}

main "$@"

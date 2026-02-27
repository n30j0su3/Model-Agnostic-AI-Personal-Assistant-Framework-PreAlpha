#!/bin/bash
#
# Sincronización BASE → PROD
# Publica versión limpia del framework al repo público
#
# IMPORTANTE: Antes de ejecutar este script, asegúrate de:
#   1. Actualizar CHANGELOG.md con los cambios de esta versión
#   2. Actualizar README.md si hay cambios significativos
#   3. Verificar que la versión en los archivos sea correcta
#   4. Ejecutar: ./sync-base-to-prod.sh [--dry-run]
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

# Verificar documentación de release
verify_release_docs() {
    log_info "Verificando documentación de release..."
    
    cd "$BASE_PATH"
    
    # Verificar que CHANGELOG.md fue actualizado
    if ! git diff HEAD --name-only | grep -q "CHANGELOG.md"; then
        log_warn "CHANGELOG.md no ha sido modificado en este commit"
        log_info "¿Olvidaste documentar los cambios?"
        echo ""
        echo "Checklist de Release:"
        echo "  [ ] Actualizar CHANGELOG.md con cambios de esta versión"
        echo "  [ ] Verificar versión correcta en README.md (ej: v0.1.1-alpha)"
        echo "  [ ] Actualizar docs/ si hay cambios de arquitectura"
        echo ""
        read -p "¿Continuar de todos modos? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Cancelado. Actualiza la documentación primero."
            exit 0
        fi
    else
        log_success "CHANGELOG.md actualizado"
    fi
    
    # Verificar versión en README.md coincide con CHANGELOG
    local readme_version=$(grep -oP 'v[0-9]+\.[0-9]+\.[0-9]+(-[a-z]+)?' README.md | head -1 || echo "unknown")
    local changelog_version=$(grep -oP '\[\K[0-9]+\.[0-9]+\.[0-9]+(-[a-z]+)?' CHANGELOG.md | head -1 || echo "unknown")
    
    log_info "README version: $readme_version"
    log_info "CHANGELOG latest: $changelog_version"
    
    if [[ "$readme_version" != "v$changelog_version" ]]; then
        log_warn "Versión en README ($readme_version) != CHANGELOG ($changelog_version)"
        read -p "¿Las versiones son correctas? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            exit 0
        fi
    fi
}

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
                echo "PRE-REQUISITOS (Checklist de Release):"
                echo "  [ ] Actualizar CHANGELOG.md con cambios de esta versión"
                echo "  [ ] Verificar versión correcta en README.md"
                echo "  [ ] Actualizar docs/ si hay cambios de arquitectura"
                echo "  [ ] Commitear todos los cambios en BASE"
                echo ""
                echo "USO:"
                echo "  $0 [--dry-run]     # Simular sin hacer cambios"
                echo "  $0                  # Ejecutar sync real"
                echo ""
                echo "PROCESO:"
                echo "  1. Verifica directorios"
                echo "  2. Valida documentación de release"
                echo "  3. Valida .gitignore"
                echo "  4. Busca archivos sensibles"
                echo "  5. Crea rama temporal"
                echo "  6. Valida archivos finales"
                echo "  7. Push a PROD (público)"
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
    verify_release_docs
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

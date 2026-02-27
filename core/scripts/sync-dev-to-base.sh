#!/bin/bash
#
# Sistema de Sincronización Segura DEV → BASE → PROD
# Framework FreakingJSON-PA - PreAlpha
#
# Este script coordina el sync desde DEV hacia BASE y PROD
# Solo sincroniza commits etiquetados con [FRAMEWORK]
#
# Uso: ./sync-dev-to-base.sh [--feature=<nombre>] [--dry-run]

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths de repos (ajústalo según tu sistema)
BASE_PATH="${BASE_PATH:-C:/ACTUAL/FreakingJSON-pa/Model-Agnostic-AI-Personal-Assistant-Framework}"
DEV_PATH="${DEV_PATH:-C:/ACTUAL/FreakingJSON-pa/Pa_Pre_alpha_Opus_4_6_DEV}"
PROD_PATH="${PROD_PATH:-C:/ACTUAL/FreakingJSON-pa/Pa_Pre_alpha_Opus_4_6}"

# Remotes
BASE_REMOTE="https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework.git"
PROD_REMOTE="https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git"

# Paths que NUNCA se sincronizan (EXCLUDE_PATHS)
EXCLUDE_PATHS=(
    'core/.context/sessions/'
    'core/.context/codebase/'
    'core/.context/MASTER.md'
    'core/.context/env_vars.json'
    'core/.context/profile.md'
    'core/.context/opencode.md'
    'core/.context/claude.md'
    'core/.context/gemini.md'
    'core/.context/workspaces/'
    'workspaces/'
    'core/agents/subagents/_local/'
    'core/skills/_local/'
    '.cache/'
    '*.tmp'
    '.last_sync'
    'TEMPO/'
    '_bmad/'
    '_bmad-output/'
    '.claude/'
    '.codex/'
    '.opencode/'
)

# Variables
FEATURE_NAME=""
DRY_RUN=false
TEMP_BRANCH=""
SYNC_DATE=$(date +%Y%m%d_%H%M%S)

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verificar que estamos en DEV
verify_dev_directory() {
    if [[ ! "$PWD" =~ "Pa_Pre_alpha_Opus_4_6_DEV" ]]; then
        log_error "Debes ejecutar este script desde el directorio DEV"
        log_info "Esperado: $DEV_PATH"
        log_info "Actual: $PWD"
        exit 1
    fi
    log_success "Directorio DEV verificado"
}

# Buscar commits con etiqueta [FRAMEWORK]
find_framework_commits() {
    log_info "Buscando commits etiquetados con [FRAMEWORK]..."
    
    # Commits desde el último sync a BASE
    local commits=$(git log BASE/main..HEAD --oneline --grep="\[FRAMEWORK\]" --reverse 2>/dev/null || true)
    
    if [ -z "$commits" ]; then
        log_warn "No se encontraron commits con [FRAMEWORK]"
        log_info "Usa: git commit -m '[FRAMEWORK] Tu mensaje' para marcar commits de framework"
        return 1
    fi
    
    log_success "Commits encontrados:"
    echo "$commits"
    echo ""
    
    # Extraer hashes
    FRAMEWORK_COMMITS=$(echo "$commits" | cut -d' ' -f1)
    COMMIT_COUNT=$(echo "$FRAMEWORK_COMMITS" | wc -l)
    
    log_info "Total de commits a sincronizar: $COMMIT_COUNT"
    return 0
}

# Validar que los commits solo tocan archivos permitidos
validate_commit_files() {
    log_info "Validando archivos de los commits..."
    
    local has_errors=false
    
    for commit in $FRAMEWORK_COMMITS; do
        local files=$(git diff-tree --no-commit-id --name-only -r "$commit")
        
        for file in $files; do
            # Verificar contra EXCLUDE_PATHS
            for exclude in "${EXCLUDE_PATHS[@]}"; do
                if [[ "$file" == $exclude* ]] || [[ "$file" == *$exclude* ]]; then
                    log_error "Commit $commit toca archivo excluido: $file"
                    log_error "Este archivo NO debe ir a BASE"
                    has_errors=true
                fi
            done
        done
    done
    
    if [ "$has_errors" = true ]; then
        log_error "Validación fallida. Corrige los commits antes de continuar."
        exit 1
    fi
    
    log_success "Validación de archivos pasada"
}

# Crear rama temporal limpia
create_temp_branch() {
    TEMP_BRANCH="sync-framework-${SYNC_DATE}"
    
    log_info "Creando rama temporal: $TEMP_BRANCH"
    
    # Desde BASE/main
    git fetch BASE main --quiet
    git checkout -b "$TEMP_BRANCH" BASE/main
    
    log_success "Rama temporal creada"
}

# Cherry-pick commits cherry_pick_commits() {
    log_info "Aplicando commits de framework..."
    
    local failed_commits=()
    
    for commit in $FRAMEWORK_COMMITS; do
        log_info "Cherry-pick: $commit"
        
        if git cherry-pick "$commit" --no-commit; then
            log_success "Commit $commit aplicado"
        else
            log_error "Conflictos en commit $commit"
            failed_commits+=("$commit")
            git cherry-pick --abort 2>/dev/null || true
        fi
    done
    
    if [ ${#failed_commits[@]} -gt 0 ]; then
        log_error "Commits fallidos: ${failed_commits[*]}"
        log_info "Debes resolver los conflictos manualmente"
        exit 1
    fi
    
    log_success "Todos los commits aplicados"
}

# Validación final exhaustiva
final_validation() {
    log_info "Validación final de seguridad..."
    
    # 1. Verificar que no hay archivos excluidos
    log_info "1. Verificando archivos excluidos..."
    local staged_files=$(git diff --cached --name-only)
    
    for file in $staged_files; do
        for exclude in "${EXCLUDE_PATHS[@]}"; do
            if [[ "$file" == $exclude* ]] || [[ "$file" == *$exclude* ]]; then
                log_error "ARCHIVO EXCLUIDO DETECTADO: $file"
                log_error "Este archivo NO debe sincronizarse a BASE"
                return 1
            fi
        done
    done
    
    # 2. Buscar patrones sensibles
    log_info "2. Buscando credenciales hardcodeadas..."
    local diff_content=$(git diff --cached)
    
    if echo "$diff_content" | grep -Ei "(api_key|apikey|password|secret|token)['\"\s]*[=:]" | grep -v "EXAMPLE\|example\|placeholder"; then
        log_warn "Posibles credenciales detectadas"
        log_warn "Revisa el diff mostrado arriba"
        read -p "¿Continuar de todos modos? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            return 1
        fi
    fi
    
    # 3. Verificar shop IDs específicos
    log_info "3. Verificando shop IDs..."
    if echo "$diff_content" | grep -E "myshopify\.com" | grep -vi "maaji\|example\|placeholder"; then
        log_warn "Shop IDs detectados"
        read -p "¿Son genéricos/de ejemplo? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            return 1
        fi
    fi
    
    # 4. Mostrar resumen
    log_info "4. Resumen de cambios:"
    echo ""
    git diff --cached --stat
    echo ""
    
    log_success "Validación final pasada"
    return 0
}

# Commit en rama temporal
commit_sync() {
    local msg="[SYNC-DEV-BASE] Framework updates ${SYNC_DATE}

Sincronización desde DEV hacia BASE

Commits incluidos:
$(git log BASE/main..HEAD --oneline)

Validaciones:
- ✅ Sin archivos de usuario (sessions, codebase)
- ✅ Sin workspaces de proyectos
- ✅ Sin agents/skills locales
- ✅ Sin credenciales hardcodeadas

Origen: Pa_Pre_alpha_Opus_4_6_DEV"

    git commit -m "$msg"
    log_success "Commit de sync creado"
}

# Push a BASE
push_to_base() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Push a BASE"
        log_info "Comando que se ejecutaría:"
        log_info "git push BASE $TEMP_BRANCH:main"
        return 0
    fi
    
    log_info "Push a BASE..."
    
    # Configurar remote si no existe
    if ! git remote | grep -q "^BASE$"; then
        git remote add BASE "$BASE_REMOTE"
        log_info "Remote BASE agregado"
    fi
    
    # Push
    if git push BASE "$TEMP_BRANCH:main"; then
        log_success "Sync a BASE completado"
        log_info "URL: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework"
    else
        log_error "Falló el push a BASE"
        exit 1
    fi
}

# Limpiar
cleanup() {
    log_info "Limpiando..."
    
    # Volver a la rama original
    git checkout - 2>/dev/null || true
    
    # Borrar rama temporal
    if [ -n "$TEMP_BRANCH" ]; then
        git branch -D "$TEMP_BRANCH" 2>/dev/null || true
    fi
    
    log_success "Limpieza completada"
}

# Menú interactivo
show_menu() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     SYNC DEV → BASE → PROD (Framework FreakingJSON)       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Este script sincroniza mejoras de framework desde DEV a BASE."
    echo ""
    echo "Requisitos:"
    echo "  • Commits etiquetados con [FRAMEWORK]"
    echo "  • Sin archivos de usuario (sessions, workspaces)"
    echo "  • Sin datos sensibles"
    echo ""
    echo "Proceso:"
    echo "  1. Detectar commits [FRAMEWORK]"
    echo "  2. Validar archivos (exclusiones)"
    echo "  3. Crear rama limpia desde BASE"
    echo "  4. Cherry-pick commits"
    echo "  5. Validación final de seguridad"
    echo "  6. Push a BASE"
    echo "  7. (Opcional) Sync a PROD"
    echo ""
}

# Main
main() {
    # Parse args
    while [[ $# -gt 0 ]]; do
        case $1 in
            --feature=*)
                FEATURE_NAME="${1#*=}"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                show_menu
                echo "Uso: $0 [--feature=nombre] [--dry-run]"
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
        log_warn "MODO DRY RUN - No se harán cambios reales"
    fi
    
    # Verificaciones iniciales
    verify_dev_directory
    
    # Buscar commits
    if ! find_framework_commits; then
        exit 0
    fi
    
    # Confirmación
    echo ""
    read -p "¿Continuar con el sync? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log_info "Cancelado por el usuario"
        exit 0
    fi
    
    # Proceso
    validate_commit_files
    create_temp_branch
    cherry_pick_commits
    
    if ! final_validation; then
        log_error "Validación final fallida"
        cleanup
        exit 1
    fi
    
    commit_sync
    push_to_base
    
    # Preguntar por PROD
    echo ""
    read -p "¿Sincronizar también a PROD? (yes/no): " prod_confirm
    if [[ "$prod_confirm" == "yes" ]]; then
        log_info "Ejecutando sync a PROD..."
        # Llamar al script de BASE→PROD
        if [ -f "./sync-base-to-prod.sh" ]; then
            ./sync-base-to-prod.sh
        else
            log_error "No se encontró sync-base-to-prod.sh"
        fi
    fi
    
    cleanup
    
    echo ""
    log_success "¡Sincronización completada!"
}

# Ejecutar
main "$@"

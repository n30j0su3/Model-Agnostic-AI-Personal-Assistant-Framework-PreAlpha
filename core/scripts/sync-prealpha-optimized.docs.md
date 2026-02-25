# Documentación de Mejoras - sync-prealpha-optimized.py

## Resumen Ejecutivo

Esta versión optimizada del sincronizador PreAlpha introduce **5 mejoras principales** que aumentan la seguridad, eficiencia y usabilidad del proceso de sincronización.

---

## 🛡️ Mejora 1: Protección de Directorios `_local/`

### Problemática
Los directorios `_local/` contienen agentes y skills específicos del entorno de desarrollo que no deben sobrescribirse durante la sincronización.

### Solución Implementada

```python
PROTECTED_DIRS = {
    "core/.context/sessions",
    "core/.context/codebase",
    "core/.context/workspaces",           # ← NUEVO
    "core/agents/subagents/_local",       # ← NUEVO
    "core/skills/_local",                 # ← NUEVO
    "workspaces",
}
```

### Beneficios
- ✅ Protege agentes locales de desarrollo
- ✅ Protege skills locales y personalizadas
- ✅ Mantiene workspaces locales intactos
- ✅ No pierde configuraciones específicas de DEV

---

## ✅ Mejora 2: Validación Pre-Sync de Recursos Críticos

### Problemática
Al sincronizar DEV, no había verificación de que los recursos críticos existieran antes de modificarlos.

### Solución Implementada

```python
def validate_critical_resources(dest_dir: Path, reporter: ExtendedSyncReporter) -> bool:
    """Verifica recursos críticos antes de sincronizar"""
    CRITICAL_RESOURCES = [
        "core/.context/MASTER.md",
        "core/.context/navigation.md", 
        "core/agents/pa-assistant.md",
    ]
    # Verifica existencia y reporta faltantes
```

### Funcionamiento
1. Antes de iniciar sync en modo DEV, verifica que existan archivos críticos
2. Muestra estado de cada recurso: `[OK]` o `[ALERTA]`
3. Verifica directorios protegidos
4. Continúa con advertencia si faltan recursos (no bloquea)

### Beneficios
- ✅ Alerta temprana de problemas
- ✅ Evita sincronizaciones sobre instalaciones corruptas
- ✅ Facilita debugging de entornos

---

## ⚡ Mejora 3: Optimización de Copia de Archivos

### Problemática
El copiado original no manejaba errores de forma granular y no preservaba todos los metadatos.

### Solución Implementada

#### Clase FileCopyManager
```python
class FileCopyManager:
    def copy_file(self, src: Path, dest: Path, preserve_metadata: bool = True) -> CopyResult:
        # Usa shutil.copy2 para preservar metadatos completos
        # Manejo específico de excepciones:
        #   - PermissionError
        #   - FileNotFoundError  
        #   - shutil.Error
        #   - Exception general
```

#### Manejo de Errores por Archivo
```python
try:
    shutil.copy2(src, dest)  # Preserva: modo, bits, hora acceso/modificación
except PermissionError:
    return CopyResult(success=False, error_message="Sin permisos...")
except FileNotFoundError:
    return CopyResult(success=False, error_message="Archivo no encontrado...")
# ... etc
```

#### ProgressTracker
```python
class ProgressTracker:
    def get_eta(self) -> Optional[str]:
        # Calcula tiempo estimado restante basado en promedio
        
    def get_progress_percentage(self) -> float:
        # Retorna porcentaje de avance
```

### Beneficios
- ✅ Un archivo fallido no detiene todo el proceso
- ✅ Preserva metadatos completos (timestamps, permisos)
- ✅ Muestra progreso en tiempo real (cada 100 archivos)
- ✅ Estimación de tiempo restante (ETA)
- ✅ Estadísticas detalladas de copia

---

## 📊 Mejora 4: Reporte Mejorado con Categorización

### Problemática
El reporte original mostraba archivos sin clasificar, dificultando la revisión.

### Solución Implementada

#### Categorización Automática
```python
class FileCategory(Enum):
    SKILL = "skills"
    AGENT = "agentes"
    DOCS = "docs"
    CONFIG = "config"
    SCRIPT = "scripts"
    CONTEXT = "context"
    OTHER = "otros"

@staticmethod
def get_file_category(file_path: str) -> FileCategory:
    # Categoriza según path y extensión
```

#### Reporte por Categorías
```
[+] ARCHIVOS NUEVOS (15)

  [SKILLS] (8):
    core/skills/dashboard-pro/manifest.json (2.3 KB)
    core/skills/dashboard-pro/main.py (15.1 KB)
    ... y 6 más

  [AGENTES] (3):
    core/agents/pa-assistant.md (45.2 KB)
    ...

  [DOCS] (4):
    docs/api.md (12.8 KB)
    ...
```

#### Métricas Adicionales
- **Bytes transferidos**: Total acumulado con formato legible (KB, MB, GB)
- **Tiempo transcurrido**: Desde inicio hasta final
- **Estadísticas de copia**: Exitosas vs Fallidas

### Beneficios
- ✅ Visión clara de qué tipo de archivos cambiaron
- ✅ Facilita review de cambios
- ✅ Identifica rápidamente problemas por categoría
- ✅ Métricas útiles para debugging de performance

---

## 🎯 Mejora 5: Modo Skill-Only

### Problemática
Para actualizar una sola skill había que sincronizar todo el framework.

### Solución Implementada

#### Nuevo Argumento CLI
```bash
python sync-prealpha-optimized.py --mode=dev --skill=dashboard-pro
```

#### Filtrado Inteligente
```python
def should_include_for_skill(file_path: str, skill_name: str) -> bool:
    # Incluye archivos en /skills/{skill_name}/
    # Incluye archivos relacionados (nombre en path)
    # Siempre incluye archivos core/config
```

#### Comportamiento
1. Solo procesa archivos relacionados con la skill especificada
2. Omite archivos de otras skills
3. No elimina archivos en destino (evita limpieza accidental)
4. Incluye archivos de configuración necesarios

### Ejemplos de Uso

```bash
# Sincronizar solo skill de dashboard
python sync-prealpha-optimized.py --mode=dev --skill=dashboard-pro

# Preview de cambios de una skill
python sync-prealpha-optimized.py --mode=dev --skill=pdf-parser --dry-run

# Sincronizar skill en producción
python sync-prealpha-optimized.py --mode=prod --skill=api-connector
```

### Beneficios
- ✅ Updates rápidos sin tocar todo el framework
- ✅ Reduce tiempo de sincronización significativamente
- ✅ Menor riesgo de cambios no deseados
- ✅ Ideal para desarrollo iterativo de skills

---

## 📋 Guía de Uso

### Comandos Básicos

```bash
# Preview completo
python sync-prealpha-optimized.py --mode=all --dry-run

# Aplicar a producción
python sync-prealpha-optimized.py --mode=prod

# Aplicar a desarrollo con verbose
python sync-prealpha-optimized.py --mode=dev --verbose

# Solo una skill
python sync-prealpha-optimized.py --mode=dev --skill=nombre-skill
```

### Opciones Disponibles

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `--mode` | prod/dev/all | `--mode=dev` |
| `--dry-run` | Preview sin aplicar | `--dry-run` |
| `--skill` | Solo una skill | `--skill=dashboard-pro` |
| `--verbose` | Logging detallado | `--verbose` |
| `--base-dir` | Ruta base custom | `--base-dir=/path` |

---

## 🔒 Seguridad y Protección

### Validaciones Implementadas

1. **Pre-sync**: Verifica recursos críticos antes de modificar
2. **Backup automático**: Directorios protegidos se respaldan antes de sync
3. **Restauración**: Si falla, restaura desde backup
4. **Errores granulares**: Un archivo fallido no detiene todo

### Directorios Protegidos

- `core/.context/sessions` - Sesiones locales
- `core/.context/codebase` - Código local indexado
- `core/.context/workspaces` - Workspaces de usuario
- `core/agents/subagents/_local` - Agentes locales
- `core/skills/_local` - Skills locales
- `workspaces` - Directorio de trabajo

---

## 📈 Performance

### Métricas Esperadas

| Escenario | Archivos | Tiempo Estimado |
|-----------|----------|-----------------|
| Sync completo | ~5000 | 30-60s |
| Sync skill única | ~50 | 2-5s |
| Dry-run completo | ~5000 | 5-10s |

### Optimizaciones

- Progreso mostrado cada 100 archivos
- ETA calculada dinámicamente
- Estadísticas de transferencia
- Manejo de errores sin bloqueos

---

## 🔄 Compatibilidad

### Backward Compatible
- ✅ Todos los comandos originales funcionan igual
- ✅ Sin breaking changes
- ✅ Mismo comportamiento por defecto

### Coexistencia
- `sync-prealpha.py` - Versión original (sin cambios)
- `sync-prealpha-optimized.py` - Versión con mejoras

---

## 📝 Changelog

### v2.0.0 - Optimizado
- [+] Protección de directorios `_local/`
- [+] Validación pre-sync de recursos críticos
- [+] Clase FileCopyManager con manejo granular de errores
- [+] ProgressTracker con ETA
- [+] Categorización de archivos en reportes
- [+] Modo skill-only (`--skill`)
- [+] Métricas de bytes transferidos
- [+] Tiempo transcurrido en reportes
- [+] Flag `--verbose` para debugging

### v1.0.0 - Original
- Sincronización básica BASE → DEV → PROD
- Protección de directorios básica
- Reporte simple de cambios

---

## 🤝 Contribución

Para reportar problemas o sugerir mejoras:
1. Usar `--verbose` para obtener logs detallados
2. Revisar archivo `.diff.md` para cambios específicos
3. Verificar directorios protegidos antes de sync

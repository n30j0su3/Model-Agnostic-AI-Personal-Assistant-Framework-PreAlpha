# Vitals Guardian - Documentación del Sistema de Protección

> **Sistema de Protección de Datos Críticos del Framework FreakingJSON**
> 
> Versión: 1.0 | Estado: Operativo

---

## Índice

1. [Resumen](#resumen)
2. [Arquitectura](#arquitectura)
3. [Componentes](#componentes)
4. [Uso](#uso)
5. [Configuración](#configuración)
6. [Recuperación de Desastres](#recuperación-de-desastres)
7. [Solución de Problemas](#solución-de-problemas)

---

## Resumen

Vitals Guardian es un sistema de **4 capas** que garantiza la protección de datos críticos del framework contra pérdida accidental. Fue creado tras un incidente donde se perdieron archivos de `workspaces/` por error.

### Filosofía

> **Permisivo con detección, restrictivo ante la duda.**

El sistema permite operaciones normales pero interviene automáticamente cuando detecta riesgo para archivos vitales.

### Archivos Protegidos

- `opencode.jsonc` - Configuración del agente CLI
- `core/.context/` - Todo el contexto del framework
- `workspaces/` - Datos de trabajo personal
- `config/` - Configuraciones
- `core/agents/` - Agentes personalizados
- `core/skills/custom/` - Skills personalizadas
- `**/OBSOLETE*/` - Histórico obsoleto

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    VITALS GUARDIAN                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Capa 1        │    │   Capa 2        │                │
│  │   Backup        │◄──►│   Interceptor   │                │
│  │   Continuo      │    │   de Comandos   │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                         │
│           ▼                       ▼                         │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Capa 3        │    │   Capa 4        │                │
│  │   Verificación  │    │   Recuperación  │                │
│  │   de Integridad │    │   Automática    │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Las 4 Capas

1. **Backup Continuo** (`vitals-guardian.py`)
   - Snapshots automáticos
   - Retención: 30 días / 50 backups
   - Sincronización con repo remoto privado

2. **Interceptor de Comandos** (`safe-executor.py`)
   - Detecta operaciones destructivas
   - Crea backup antes de ejecutar
   - Solicita confirmación para operaciones de riesgo

3. **Verificación de Integridad**
   - Hash SHA-256 de archivos vitales
   - Detección de archivos faltantes/modificados
   - Ejecución al inicio de sesión

4. **Recuperación Automática**
   - Restauración desde backup local
   - Restauración desde repo remoto
   - Verificación post-restauración

---

## Componentes

### 1. vitals-guardian.py

Script principal de protección.

**Comandos:**

```bash
# Verificar integridad
python core/scripts/vitals-guardian.py check

# Crear snapshot manual
python core/scripts/vitals-guardian.py snapshot
python core/scripts/vitals-guardian.py snapshot --reason "antes_de_cambio"

# Listar backups
python core/scripts/vitals-guardian.py list

# Restaurar desde backup
python core/scripts/vitals-guardian.py restore

# Sincronizar con repo remoto
python core/scripts/vitals-guardian.py sync
```

### 2. safe-executor.py

Interceptor de comandos destructivos.

**Uso:**

```bash
# Ejecutar comando con protección
python core/scripts/safe-executor.py -- "rm -rf workspaces/"

# Simular sin ejecutar (dry-run)
python core/scripts/safe-executor.py --dry-run -- "rm -rf temp/"

# Modo estricto (siempre confirmar)
python core/scripts/safe-executor.py --strict -- "del archivo.txt"
```

### 3. vitals-remote-setup.py

Configuración de sincronización remota.

**Uso:**

```bash
# Verificar estado
python core/scripts/vitals-remote-setup.py --check

# Configuración automática
python core/scripts/vitals-remote-setup.py --auto

# Configuración interactiva
python core/scripts/vitals-remote-setup.py
```

---

## Uso

### Flujo Diario Normal

1. **Al iniciar sesión**, el sistema verifica automáticamente la integridad
2. **Antes de operaciones destructivas**, usa `safe-executor.py`
3. **Crear snapshot manual** antes de cambios importantes

### Crear Backup Manual

```bash
python core/scripts/vitals-guardian.py snapshot --reason "antes_refactor"
```

### Restaurar Después de Pérdida

```bash
# Verificar qué archivos faltan
python core/scripts/vitals-guardian.py check

# Listar backups disponibles
python core/scripts/vitals-guardian.py list

# Restaurar desde un backup
python core/scripts/vitals-guardian.py restore
# (seleccionar número del backup)
```

### Sincronización con Repo Remoto

```bash
# Sync manual
python core/scripts/vitals-guardian.py sync

# O usar git directamente
git push vitals-backup main
```

---

## Configuración

### Archivo de Configuración

`core/.context/vitals/vitals.config.json`:

```json
{
  "vitals": [
    "opencode.jsonc",
    "core/.context/MASTER.md",
    "workspaces/",
    "..."
  ],
  "remote_repo": "https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-dev.git",
  "backup_retention_days": 30,
  "max_backups": 50,
  "auto_backup_on_destructive": true,
  "check_integrity_on_startup": true,
  "sync_to_remote": true,
  "auto_sync_after_backup": true
}
```

### Configurar Repo Remoto

1. **Verificar credenciales GitHub:**
   ```bash
   python core/scripts/vitals-remote-setup.py --check
   ```

2. **Si faltan credenciales**, configurar:
   ```bash
   git config --global credential.helper manager
   # Intentar push para guardar credenciales
   git push vitals-backup main
   ```

3. **Configurar automáticamente:**
   ```bash
   python core/scripts/vitals-remote-setup.py --auto
   ```

---

## Recuperación de Desastres

### Escenario 1: Archivos Borrados Accidentalmente

```bash
# 1. NO PANIC - Verificar backups
python core/scripts/vitals-guardian.py list

# 2. Restaurar desde último backup
python core/scripts/vitals-guardian.py restore

# 3. Verificar integridad
python core/scripts/vitals-guardian.py check
```

### Escenario 2: Repo Local Corrupto

```bash
# 1. Clonar repo desde remoto
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-dev.git vitals-recovery

# 2. Copiar backups al repo local
cp -r vitals-recovery/vitals/* /ruta/al/framework/core/.context/vitals/

# 3. Restaurar desde backup
python core/scripts/vitals-guardian.py restore
```

### Escenario 3: Disco Duro Falla

1. Instalar framework fresco desde GitHub
2. Configurar `vitals-remote-setup.py`
3. Restaurar desde repo remoto `vitals-backup`

---

## Solución de Problemas

### Error: "No se pudieron cargar credenciales"

**Causa:** Git no tiene credenciales almacenadas para GitHub.

**Solución:**
```bash
# Windows
git config --global credential.helper manager

# Mac
git config --global credential.helper osxkeychain

# Linux
git config --global credential.helper store

# Luego intentar push manual para guardar credenciales
git push vitals-backup main
```

### Error: "Autenticación fallida"

**Causa:** Token de GitHub expirado o revocado.

**Solución:**
1. Generar nuevo token en https://github.com/settings/tokens
2. Intentar push nuevamente
3. Ingresar token como contraseña

### Error: "Remote vitals-backup no existe"

**Solución:**
```bash
python core/scripts/vitals-remote-setup.py --auto
```

### Backup muy lento

**Causa:** Demasiados archivos en workspaces/ o sessions/

**Solución:**
- Excluir directorios no esenciales en `vitals.config.json`
- Limpiar backups antiguos: `python core/scripts/vitals-guardian.py list`

---

## Referencias

- `core/scripts/vitals-guardian.py` - Script principal
- `core/scripts/safe-executor.py` - Interceptor de comandos
- `core/scripts/vitals-remote-setup.py` - Configuración remota
- `core/.context/vitals/` - Directorio de backups y config

---

> **Recuerda:** *
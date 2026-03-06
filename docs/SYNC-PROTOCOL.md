# Sync Protocol

> "El flujo correcto es la diferencia entre el caos y la armonía."

**Última actualización**: 2026-03-06  
**Versión**: 1.0.0  
**Autor**: FreakingJSON-PA

---

## 🎯 Propósito

Documentar el protocolo de sincronización entre los 3 ambientes del framework:
- **BASE** → Código fuente (repo privado)
- **DEV** → Testing interno (repo privado)
- **PROD** → Versión pública (repo público)

---

## 🌍 Ambientes

### Resumen

| Ambiente | Ruta Local | Repo Remoto | Privacidad | Propósito |
|----------|-----------|-------------|------------|-----------|
| **BASE** | `C:\ACTUAL\FreakingJSON-pa\Model-Agonistic-AI-Personal-Assistant-Framework` | `github.com/n30j0su3/Model-Agonistic-...-Framework.git` | 🔒 Privado | Código fuente del framework (todo el contexto de desarrollo) |
| **DEV** | `C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV` | `github.com/n30j0su3/Model-Agonistic-...-Framework-dev.git` | 🔒 Privado | Versión PROD-Ready pero uso INTERNO (preserva datos/credenciales/proyectos específicos) |
| **PROD** | `C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6` | `github.com/n30j0su3/Model-Agonistic-...-Framework-PreAlpha.git` | 🌍 Público | Versión CLEAN (solo archivos autorizados/saneados) |

### Detalle por Ambiente

#### BASE (Código Fuente)

**Contiene**:
- ✅ Todo el código fuente
- ✅ `opencode.jsonc` (completo, con credenciales)
- ✅ `opencode.jsonc.CLEAN-PROD` (versión saneada)
- ✅ Backlog y docs internos (`docs/backlog.md`, etc.)
- ✅ Scripts de sync y automatización
- ✅ Workspaces (estructura base/templates)

**No contiene**:
- ❌ Sessions del usuario
- ❌ Codebase personal (ideas, recordatorios)

#### DEV (Testing Interno)

**Contiene**:
- ✅ Todo lo de BASE (sincronizado)
- ✅ `opencode.jsonc` (completo, con credenciales)
- ✅ Workspaces locales del usuario (protegidos)
- ✅ Sessions locales (protegidas)
- ✅ Codebase personal (protegido)
- ✅ Agentes/skills locales en `_local/` (protegidos)

**Protegido (nunca se sobrescribe con sync)**:
- `core/.context/sessions`
- `core/.context/codebase`
- `core/.context/workspaces`
- `core/agents/subagents/_local`
- `core/skills/_local`
- `workspaces` (root)

#### PROD (Público)

**Contiene**:
- ✅ `opencode.jsonc` (CLEAN-PROD, sin credenciales)
- ✅ `README-simple.md` → `README.md` (versión user-friendly)
- ✅ Docs públicos (sin backlog, sin docs internos)
- ✅ Skills públicas
- ✅ Agentes públicos

**NO contiene**:
- ❌ Credenciales o API keys
- ❌ `backlog.md` ni docs internos
- ❌ Workspaces del usuario
- ❌ Sessions o codebase personal
- ❌ Agentes/skills locales (`_local/`)

---

## 🔄 Flujos de Sync

### Flujo Principal: BASE → DEV → PROD

```
┌─────────────────────────────────────────────────────────────┐
│                    SYNC WORKFLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  BASE (Código Fuente)                                       │
│  🔒 Privado: github.com/.../Framework.git                  │
│                                                              │
│  ↓ python sync-prealpha.py --mode=dev                      │
│    (copia completo, incluye credenciales)                  │
│                                                              │
│  DEV (Test Interno)                                         │
│  🔒 Privado: github.com/.../Framework-dev.git              │
│  ✅ Protegidos: sessions, codebase, workspaces, _local/    │
│                                                              │
│  ↓ python sync-prealpha.py --mode=prod                     │
│    (copia CLEAN-PROD, sanea, valida)                       │
│                                                              │
│  PROD (Público)                                             │
│  🌍 Público: github.com/.../Framework-PreAlpha.git         │
│  ✅ Auto-commit con validación de seguridad                │
│                                                              │
│  ↓ git add + git commit + git push (auto)                  │
│                                                              │
│  REMOTO-PÚBLICO                                             │
│  🌍 Visible para todos                                      │
└─────────────────────────────────────────────────────────────┘
```

### Flujo Alternativo: DEV → BASE → PROD

**Cuándo usar**: Desarrollaste una feature en DEV y quieres subirla a BASE antes de publicar.

```
DEV (feature completada)
  ↓ (commit manual en DEV)
  ↓ git push a repo DEV
  ↓ (validación en BASE)
BASE (recibe feature)
  ↓ python sync-prealpha.py --mode=prod
PROD (público con nueva feature)
```

---

## 🛠 Comandos

### Sync BASE → DEV

```bash
cd C:\ACTUAL\FreakingJSON-pa\Model-Agonistic-...-Framework
python core/scripts/sync-prealpha.py --mode=dev
```

**Qué se copia**:
- ✅ TODO el código fuente
- ✅ `opencode.jsonc` (completo, con credenciales)
- ✅ `backlog.md`, docs internos
- ✅ `workspaces/` (estructura base, NO se sobrescribe si ya existe en DEV)

**Validaciones**:
- ✅ Directorios protegidos no se sobrescriben
- ✅ `CRITICAL_RESOURCES` existen en destino

**Post-sync**:
- ⚠️ NO hace auto-commit (DEV es interno)
- ⚠️ Usuario decide cuándo commitear

---

### Sync BASE → PROD

```bash
cd C:\ACTUAL\FreakingJSON-pa\Model-Agonistic-...-Framework
python core/scripts/sync-prealpha.py --mode=prod
```

**Qué se copia**:
- ✅ `opencode.jsonc.CLEAN-PROD` → renombrado a `opencode.jsonc`
- ✅ `README-simple.md` → renombrado a `README.md`
- ✅ Docs públicos (excluye backlog, docs internos)
- ✅ Skills y agentes públicos

**NO se copia**:
- ❌ `workspaces/` (interno del usuario)
- ❌ `docs/backlog.md`
- ❌ `docs/backlog.view.md`
- ❌ Credenciales o API keys

**Validaciones POST-sync** (auto):
```python
1. Verificar opencode.jsonc sin credenciales
   - Busca: pk_, sk_, YOUR_GITHUB_TOKEN, api_key, PRIVATE_API_KEY
   - Si encuentra: ABORTA commit

2. Verificar README.md es user-friendly
   - Si es técnico: Copia README-simple.md → README.md

3. Auto-commit (si --auto-commit=True)
   - git add .
   - git commit -m "chore(release): sync v{VERSION} - CLEAN-PROD"
   - git push
```

**Post-sync**:
- ✅ Auto-commit y push (default: True para PROD)
- ✅ Validación de seguridad automática

---

### Dry-Run (Preview)

```bash
# Preview BASE → PROD
python core/scripts/sync-prealpha.py --mode=prod --dry-run

# Preview BASE → DEV
python core/scripts/sync-prealpha.py --mode=dev --dry-run
```

**Output**:
- Lista de archivos que se copiarían
- Archivos ignorados
- Archivos protegidos
- Advertencias de seguridad

---

### Sync de Solo Skills

```bash
# Solo una skill específica
python core/scripts/sync-prealpha-optimized.py --mode=dev --skill=dashboard-pro

# Múltiples skills
python core/scripts/sync-prealpha-optimized.py --mode=dev --skill=dashboard-pro --skill=pdf
```

---

## 📋 Directorios Protegidos

### En DEV (Nunca se sobrescriben)

| Directorio | ¿Por qué? |
|------------|-----------|
| `core/.context/sessions` | Sesiones diarias del usuario |
| `core/.context/codebase` | Ideas, recordatorios, contexto personal |
| `core/.context/workspaces` | Workspaces locales del usuario |
| `core/agents/subagents/_local` | Agentes locales de DEV (no en BASE) |
| `core/skills/_local` | Skills locales de DEV (no en BASE) |
| `workspaces` (root) | Proyectos específicos del usuario |

### En PROD (Excluidos del sync)

| Directorio/Archivo | ¿Por qué? |
|-------------------|-----------|
| `workspaces/` | Interno del usuario |
| `core/.context/sessions/` | Datos personales |
| `core/.context/codebase/` | Contexto personal |
| `docs/backlog.md` | Doc interno de desarrollo |
| `docs/backlog.view.md` | Doc interno de desarrollo |
| `core/agents/subagents/_local/` | Agentes locales |
| `core/skills/_local/` | Skills locales |
| `opencode.jsonc` (de BASE) | Tiene credenciales, se usa CLEAN-PROD |

---

## ⚠️ Validaciones de Seguridad

### Pre-Sync (PROD)

```python
# Verificar que CLEAN-PROD existe
if not (BASE_DIR / "opencode.jsonc.CLEAN-PROD").exists():
    print("❌ ERROR: opencode.jsonc.CLEAN-PROD no existe en BASE")
    sys.exit(1)
```

### Post-Sync (PROD)

```python
# Verificar opencode.jsonc saneado
dangerous_patterns = ["pk_", "sk_", "YOUR_GITHUB_TOKEN", "api_key", "PRIVATE_API_KEY"]
for pattern in dangerous_patterns:
    if pattern in config_content:
        print(f"❌ ALERTA: {pattern} encontrado en opencode.jsonc")
        print("❌ SYNC ABORTADO: No se puede hacer commit a repo público")
        sys.exit(1)
```

---

## 🐛 Troubleshooting

### Problema: `opencode.jsonc` no aparece en repo público

**Causas posibles**:
1. Sync no se ejecutó en modo PROD
2. `opencode.jsonc.CLEAN-PROD` no existe en BASE
3. Auto-commit está deshabilitado

**Solución**:
```bash
# 1. Verificar CLEAN-PROD en BASE
dir C:\ACTUAL\FreakingJSON-pa\Model-Agonistic-...-Framework\opencode.jsonc.CLEAN-PROD

# 2. Ejecutar sync con dry-run
cd C:\ACTUAL\FreakingJSON-pa\Model-Agonistic-...-Framework
python core/scripts/sync-prealpha.py --mode=prod --dry-run

# 3. Ejecutar sync real
python core/scripts/sync-prealpha.py --mode=prod

# 4. Verificar en PROD local
cd C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6
cat opencode.jsonc | findstr "pk_"

# 5. Si está limpio, commit manual
git add opencode.jsonc
git commit -m "chore: update opencode.jsonc"
git push
```

---

### Problema: Workspaces se sobrescribe en DEV

**Causa**: `workspaces/` debería estar en `PROTECTED_DIRS` pero no está.

**Solución**:
```python
# Verificar en sync-prealpha.py
PROTECTED_DIRS = {
    "core/.context/sessions",
    "core/.context/codebase",
    "core/.context/workspaces",  # ✅ Debe estar
    "core/agents/subagents/_local",
    "core/skills/_local",
    "workspaces",  # ✅ Debe estar
}
```

---

### Problema: Backlog.md aparece en PROD

**Causa**: `docs/backlog.md` no está en `PROD_ONLY_IGNORE_PATTERNS`.

**Solución**:
```python
# Agregar en sync-prealpha.py
PROD_ONLY_IGNORE_PATTERNS = {
    "docs/backlog.md",
    "docs/backlog.view.md",
    # ... otros docs internos
}
```

---

### Problema: Auto-commit falla

**Causas posibles**:
1. Git no está en PATH
2. No hay cambios para commitear
3. Usuario no tiene permisos de push

**Solución**:
```bash
# 1. Verificar Git
git --version

# 2. Verificar cambios
git status --porcelain

# 3. Commit manual
cd C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6
git add .
git commit -m "chore(release): sync manual"
git push
```

---

## 📊 Estadísticas de Sync

| Métrica | Valor |
|---------|-------|
| **Último sync exitoso** | Por registrar |
| **Archivos sincronizados** | Por registrar |
| **Archivos ignorados** | Por registrar |
| **Advertencias de seguridad** | 0 (esperado) |

---

## 🔗 Referencias

- [scripts/sync-prealpha.py](../core/scripts/sync-prealpha.py) — Script principal
- [scripts/sync-prealpha-optimized.py](../core/scripts/sync-prealpha-optimized.py) — Versión optimizada
- [RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md) — Checklist de release
- [docs/backlog.md](./backlog.md) — Backlog del framework

---

## 📝 Changelog

### v1.0.0 (2026-03-06)

- ✅ Documentación inicial de Sync Protocol
- ✅ 3 ambientes definidos (BASE/DEV/PROD)
- ✅ Directorios protegidos documentados
- ✅ Validaciones de seguridad especificadas
- ✅ Troubleshooting incluido

---

> *"El conocimiento verdadero trasciende a lo público."*
> 
> *"I own my context. I am FreakingJSON."*

---

*Sync Protocol v1.0.0 - FreakingJSON Personal Assistant Framework*

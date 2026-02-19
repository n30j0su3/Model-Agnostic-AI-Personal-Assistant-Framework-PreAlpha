# Configuración de Agents - PA Framework

## Resumen

El PA Framework utiliza **dos agentes principales** configurados según el entorno:

| Agente | Entorno | Personalidad | Uso |
|--------|---------|--------------|-----|
| **FreakingJSON** | Desarrollo (Base + PreAlpha-DEV) | Cool, creativo (temp 0.1) | Desarrollo interno, sesiones locales |
| **FreakingJSON-PA** | Producción (PreAlpha-Prod) | Formal, técnico (temp 0.2) | Release público, usuarios externos |

## Ubicación de Archivos

```
.opencode/
├── config.json              # Configuración del agent por defecto
└── agent/
    ├── FreakingJSON.md      # Definición del agente cool
    └── pa-assistant.md      # Definición del agente formal (FreakingJSON-PA)
```

## Configuración por Repositorio

### 1. Proyecto Base (Desarrollo)

**Ubicación:** `Model-Agnostic-AI-Personal-Assistant-Framework/.opencode/config.json`

```json
{
  "agent": "FreakingJSON"
}
```

**Propósito:** 
- Desarrollo activo del framework
- Acceso al backlog completo
- Estilo creativo y personal
- Filosofía: "I own my context. I am FreakingJSON."

### 2. PreAlpha-DEV (Testing)

**Ubicación:** `Pa_Pre_alpha_Opus_4_6_DEV/.opencode/config.json`

```json
{
  "agent": "FreakingJSON"
}
```

**Propósito:**
- Testing con credenciales reales
- Mismo comportamiento que el base
- Backlog disponible para planificación
- Preparación antes de producción

### 3. PreAlpha-Prod (Producción)

**Ubicación:** `Pa_Pre_alpha_Opus_4_6/.opencode/config.json`

```json
{
  "agent": "FreakingJSON-PA"
}
```

**Propósito:**
- Release público
- Comportamiento formal y técnico
- Sin acceso a backlog interno
- Sin credenciales en configuración

## Diferencias entre Agents

### FreakingJSON (Desarrollo)

**Características:**
- **Temperatura:** 0.1 (muy creativo)
- **Estilo:** "Supréme Orchestrator", personal, cool
- **Contexto:** Acceso completo a backlog y documentación interna
- **Frase clave:** "I own my context. I am FreakingJSON."
- **Subagentes:** context-scout, session-manager, doc-writer
- **Permisos:** Más flexibles para desarrollo

**Casos de uso:**
- Desarrollo de nuevas features
- Debugging y testing
- Planificación de roadmap
- Sesiones de desarrollo diarias

### FreakingJSON-PA (Producción)

**Características:**
- **Temperatura:** 0.2 (balanceado)
- **Estilo:** Formal, técnico, profesional
- **Contexto:** Solo documentación pública del framework
- **Enfoque:** Usuario final, experiencia optimizada
- **Subagentes:** context-scout, session-manager, doc-writer
- **Permisos:** Más restrictivos para seguridad

**Casos de uso:**
- Usuarios finales del framework
- Demostraciones públicas
- Documentación y tutoriales
- Soporte y troubleshooting

## Cambiar el Agent Manualmente

Si necesitas cambiar el agente temporalmente:

```bash
# Editar el archivo de configuración
nano .opencode/config.json

# Cambiar el valor de "agent"
{
  "agent": "FreakingJSON"      # o "FreakingJSON-PA"
}
```

**Nota:** Los cambios en `config.json` son locales al repositorio. El script `sync-prealpha.py` puede sobrescribirlos, así que verifica la configuración después de sincronizar.

## Workflow Recomendado

```
┌─────────────────────────────────────────────────────────────┐
│  DESARROLLO (Base + PreAlpha-DEV)                          │
│  Agente: FreakingJSON                                       │
│  • Trabajo diario                                           │
│  • Planificación con backlog                                │
│  • Testing con credenciales                                 │
│  • Estilo creativo y personal                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ Sync + Validación
┌─────────────────────────────────────────────────────────────┐
│  PRODUCCIÓN (PreAlpha-Prod)                                │
│  Agente: FreakingJSON-PA                                    │
│  • Release público                                          │
│  • Sin backlog interno                                      │
│  • Sin credenciales                                         │
│  • Estilo formal y profesional                              │
└─────────────────────────────────────────────────────────────┘
```

## Mantenimiento

### Después de Sincronización

Después de ejecutar `sync-prealpha.py`, verifica que los configs sean correctos:

```bash
# Verificar PreAlpha-DEV
cat Pa_Pre_alpha_Opus_4_6_DEV/.opencode/config.json
# Debe mostrar: {"agent": "FreakingJSON"}

# Verificar PreAlpha-Prod
cat Pa_Pre_alpha_Opus_4_6/.opencode/config.json
# Debe mostrar: {"agent": "FreakingJSON-PA"}
```

### Agregar Nuevos Agents

Para agregar un nuevo agente personalizado:

1. Crear archivo en `.opencode/agent/mi-agente.md`
2. Seguir el formato YAML frontmatter
3. Actualizar `config.json` si es el agente por defecto
4. Documentar el nuevo agente en este archivo

## Verificación Post-Sincronización

Después de ejecutar `sync-prealpha.py`, es importante verificar que la configuración de agents se mantenga correcta:

### Checklist después de sync

```bash
# 1. Verificar PreAlpha-DEV (debe ser FreakingJSON)
cat Pa_Pre_alpha_Opus_4_6_DEV/.opencode/config.json

# 2. Verificar PreAlpha-Prod (debe ser FreakingJSON-PA)
cat Pa_Pre_alpha_Opus_4_6/.opencode/config.json

# 3. Verificar que ambos agents existen
ls Pa_Pre_alpha_Opus_4_6/.opencode/agent/
# Debe mostrar: FreakingJSON.md, pa-assistant.md (FreakingJSON-PA)
```

### Si la configuración se perdió

Si el sync sobrescribió los configs, restáuralos manualmente:

```bash
# Para PreAlpha-DEV
echo '{"agent": "FreakingJSON"}' > Pa_Pre_alpha_Opus_4_6_DEV/.opencode/config.json

# Para PreAlpha-Prod
echo '{"agent": "FreakingJSON-PA"}' > Pa_Pre_alpha_Opus_4_6/.opencode/config.json
```

Luego commit y push:
```bash
cd Pa_Pre_alpha_Opus_4_6
git add .opencode/config.json
git commit -m "fix: restaurar configuración de agent"
git push origin main

cd Pa_Pre_alpha_Opus_4_6_DEV
git add .opencode/config.json
git commit -m "fix: restaurar configuración de agent"
git push origin dev
```

## Referencias

- [FreakingJSON Agent Definition](../.opencode/agent/FreakingJSON.md)
- [FreakingJSON-PA Agent Definition](../.opencode/agent/pa-assistant.md)
- [Sync Process](../OBSOLETE/docs/PREALPHA-SYNC-PROCESS.md)

---

**Versión:** 1.0  
**Actualizado:** 2025-02-11  
**Framework:** PA Framework PreAlpha

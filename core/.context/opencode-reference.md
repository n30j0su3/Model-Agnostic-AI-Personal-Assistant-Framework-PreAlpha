# OpenCode Reference

> "Conocer las herramientas es dominar el flujo de trabajo."

**Última actualización**: 2026-03-06  
**Versión OpenCode**: Latest (2026-03)

---

## 📚 Documentación Oficial

| Recurso | URL | Propósito |
|---------|-----|-----------|
| **Homepage** | https://opencode.ai/docs/ | Documentación principal |
| **Commands** | https://opencode.ai/docs/commands/ | Comandos custom (nuestros `/pa-*`) |
| **Agents** | https://opencode.ai/docs/agents/ | Configuración de agentes |
| **Models** | https://opencode.ai/docs/models/ | Modelos disponibles |
| **MCP Servers** | https://opencode.ai/docs/mcp-servers/ | Model Context Protocol |
| **Skills** | https://opencode.ai/docs/skills/ | Agent Skills |
| **CLI** | https://opencode.ai/docs/cli/ | Comandos CLI |
| **TUI** | https://opencode.ai/docs/tui/ | Terminal UI |
| **Config** | https://opencode.ai/docs/config/ | Configuración |
| **Rules** | https://opencode.ai/docs/rules/ | Reglas y permisos |

---

## ⚠️ Overlaps Detectados

### Comandos Built-in de OpenCode (NO Override)

| Comando | Propósito OpenCode | Nuestro Estado |
|---------|-------------------|----------------|
| `/init` | Inicializa repositorio | ❌ NO USAR |
| `/undo` | Deshacer última acción | ❌ NO USAR |
| `/redo` | Rehacer acción | ❌ NO USAR |
| `/share` | Compartir sesión | ❌ NO USAR |
| `/help` | Ayuda de OpenCode | ❌ Renombrado a `/pa-help` |
| `/compact` | Compactar contexto | ❌ NO USAR |
| `/models` | Listar modelos | ❌ NO USAR |
| `/auth` | Autenticación | ❌ NO USAR |
| `/session` | Sesión TUI de OpenCode | ⚠️ Diferente propósito (ver abajo) |
| `/stats` | Estadísticas OpenCode | ❌ NO USAR |
| `/export` | Exportar sesión | ❌ NO USAR |
| `/import` | Importar sesión | ❌ NO USAR |
| `/web` | Iniciar servidor web | ❌ NO USAR |
| `/serve` | Servidor headless | ❌ NO USAR |
| `/run` | Ejecutar prompt | ❌ NO USAR |
| `/status` | ❌ NO EXISTE en OpenCode | ✅ Nuestro comando (renombrado a `/pa-status`) |

### Diferencia Crítica: `/session`

| Característica | OpenCode `/session` | Nuestro `/session` |
|----------------|---------------------|-------------------|
| **Propósito** | Gestionar sesiones TUI interactivas | Gestionar sesiones .md locales |
| **Almacenamiento** | Session state en memoria/UI | Archivos `.md` en `core/.context/sessions/` |
| **Persistencia** | Temporal (sesión CLI) | Permanente (archivos locales) |
| **Comandos** | `--continue`, `--fork` | `create`, `show`, `close` |
| **Agente** | N/A (built-in) | `@session-manager` |

**Conclusión**: Pueden coexistir porque tienen propósitos diferentes, pero el usuario debe entender la distinción.

---

## ✅ Nuestros Comandos Custom

| Comando | Archivo | Agente | Propósito |
|---------|---------|--------|-----------|
| `/pa-status` | `.opencode/commands/pa-status.md` | FreakingJSON | Estado del framework (KPIs, métricas) |
| `/session` | `.opencode/commands/session.md` | session-manager | Sesiones diarias .md (NO OpenCode TUI) |
| `/save` | `.opencode/commands/save.md` | doc-writer | Guardado de contexto |
| `/ideas` | `.opencode/commands/ideas.md` | FreakingJSON | Gestión de ideas |
| `/pending` | `.opencode/commands/pending.md` | task-management | Gestión de pendientes |
| `/pa-help` | `.opencode/commands/pa-help.md` | FreakingJSON | Ayuda del framework |

---

## 🛠 Configuración OpenCode

### Archivos en `.opencode/`

| Archivo | Propósito |
|---------|-----------|
| `config.json` | Agente por defecto |
| `commands/` | Comandos custom (.md files) |
| `agent/` | Definición de agentes custom |
| `context/` | Contexto específico del proyecto |

### Nuestro `opencode.jsonc`

**Ubicación**: Raíz del proyecto

**Contiene**:
- MCP servers configurados (Context7, Klaviyo, TripleWhale, GitHub)
- Providers de modelos (Kimi, Model Studio, NanoGPT)
- Modelos disponibles con configuración detallada

**Versión CLEAN-PROD**: `opencode.jsonc.CLEAN-PROD`
- Sin credenciales
- Sin API keys
- Listo para repo público

---

## 📖 Estándares de Comandos Custom

### Formato Markdown Oficial

```markdown
---
description: Descripción corta del comando
agent: nombre-del-agente
model: provider/modelo (opcional)
subtask: true|false (opcional)
---

# Contenido del Prompt

Aquí va el prompt que se enviará al LLM.

Puede incluir:
- `$ARGUMENTS` → Todos los argumentos
- `$1`, `$2`, `$3` → Argumentos posicionales
- `!`comando`` → Output de shell
- `@archivo` → Contenido de archivo
```

### Ejemplo con Argumentos

```markdown
---
description: Crear componente React
agent: build
---

Crear un componente React llamado $ARGUMENTS con:
- TypeScript
- Tipado adecuado
- Estructura básica funcional
```

Uso: `/component Button`

### Ejemplo con Shell Output

```markdown
---
description: Revisar cambios recientes
---

Revisar los últimos commits:

!`git log --oneline -10`

Sugerir mejoras o identificar problemas.
```

### Ejemplo con File Reference

```markdown
---
description: Revisar componente
---

Revisar el archivo @src/components/Button.tsx

Identificar:
- Problemas de rendimiento
- Mejoras de accesibilidad
- Patrones recomendados
```

---

## 🔗 Recursos Adicionales

### Comunidad y Soporte

| Recurso | URL |
|---------|-----|
| **Discord** | https://opencode.ai/discord |
| **GitHub** | https://github.com/anomalyco/opencode |
| **Issues** | https://github.com/anomalyco/opencode/issues |
| **NPM** | https://www.npmjs.com/package/opencode |

### Model Providers

| Provider | URL |
|----------|-----|
| **Models.dev** | https://models.dev |
| **OpenAI** | https://platform.openai.com |
| **Anthropic** | https://console.anthropic.com |
| **Google AI** | https://makersuite.google.com |

---

## 📝 Notas de Integración

### Comandos que Sobreescritura Built-ins

> **Nota**: Los comandos custom pueden sobrescribir built-ins de OpenCode si tienen el mismo nombre.

**Ejemplo**: Si creas `.opencode/commands/help.md`, sobrescribe `/help` de OpenCode.

**Nuestra decisión**: Renombrar a `/pa-help` para evitar confusión.

### Agents Custom vs Built-in

OpenCode tiene agentes built-in (`plan`, `build`, etc.). Nuestros agentes del framework:
- `FreakingJSON` → Agente principal
- `session-manager` → Gestión de sesiones
- `doc-writer` → Documentación
- `feature-architect` → Arquitectura de features

**Configuración**: Ver `.opencode/agent/` para definiciones custom.

---

## 🎯 Mejores Prácticas

### Para Comandos Custom

1. **Nombres únicos**: Evitar overlaps con built-ins
2. **Descripciones claras**: El usuario debe entender qué hace el comando
3. **MVI**: Minimal Viable Information en el prompt
4. **Agentes específicos**: Delegar al agente apropiado
5. **Documentación**: Referenciar docs oficiales cuando aplique

### Para Configuración

1. **CLEAN-PROD**: Mantener versión sin credenciales para repo público
2. **MCP servers**: Solo habilitar los necesarios
3. **Models**: Configurar modelos por defecto apropiados
4. **Agents**: Definir agentes custom en `.opencode/agent/`

---

*Para documentación del framework FreakingJSON: `docs/README.md`*  
*Para configuración de agentes: `core/agents/AGENTS.md`*

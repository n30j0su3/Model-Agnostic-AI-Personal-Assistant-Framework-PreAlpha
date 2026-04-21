# CLI Integration Guide

> **Para usuarios de**: OpenCode, Claude Code, Gemini CLI, Qwen Code, Codex

---

## 🎯 Overview

El PA Framework captura mensajes automáticamente cuando usas CLIs de AI. Solo necesitas configurar el hook.

---

## 🔧 Integración por CLI

### OpenCode (NanoGPT)

**Archivo**: `~/.config/opencode/hooks.json` (o crear)

```json
{
  "pre_prompt": "python /path/to/pa-framework/core/scripts/message_hook.py --capture user \"$PROMPT\"",
  "post_response": "python /path/to/pa-framework/core/scripts/message_hook.py --capture assistant \"$RESPONSE\""
}
```

**Alternativa (ACP mode)**:
```bash
# En opencode.jsonc, añadir MCP server:
{
  "mcpServers": {
    "pa-framework": {
      "command": "python",
      "args": ["core/scripts/message_hook.py", "--mcp"]
    }
  }
}
```

---

### Claude Code (Anthropic)

**Opción 1: Shell hook**

```bash
# ~/.bashrc o ~/.zshrc
export CLAUDE_PRE_HOOK='python /path/to/pa-framework/core/scripts/message_hook.py --capture user'
export CLAUDE_POST_HOOK='python /path/to/pa-framework/core/scripts/message_hook.py --capture assistant'
```

**Opción 2: Python skill**

Claude Code puede cargar skills automáticamente. Crear:
```
~/.claude/skills/pa-capture.md
```

```markdown
---
name: pa-capture
trigger: on_message
---

after_every_message:
  - action: python_capture
    script: /path/to/pa-framework/core/scripts/message_hook.py
    args: ["--capture", "$role", "$content"]
```

---

### Gemini CLI (Google)

**Config**: `~/.gemini/config.yaml`

```yaml
hooks:
  pre_send:
    command: python
    args:
      - /path/to/pa-framework/core/scripts/message_hook.py
      - --capture
      - user
      - "${prompt}"
  post_receive:
    command: python
    args:
      - /path/to/pa-framework/core/scripts/message_hook.py
      - --capture
      - assistant
      - "${response}"
```

---

### Qwen Code (Alibaba)

**Config**: `~/.qwen/hooks.py`

```python
import subprocess

def on_user_input(text):
    subprocess.run([
        "python", 
        "/path/to/pa-framework/core/scripts/message_hook.py",
        "--capture", "user", text
    ])

def on_ai_response(text):
    subprocess.run([
        "python",
        "/path/to/pa-framework/core/scripts/message_hook.py",
        "--capture", "assistant", text
    ])
```

---

### Codex (OpenAI)

**Config**: `~/.codexrc`

```bash
# Hook configuration
HOOK_PRE_PROMPT="python /path/to/pa-framework/core/scripts/message_hook.py --capture user"
HOOK_POST_RESPONSE="python /path/to/pa-framework/core/scripts/message_hook.py --capture assistant"
```

---

## 📁 Paths por Platform

| **Platform** | PA Framework Path |
|--------------|-------------------|
| Windows | `C:\Users\<user>\pa-framework\` |
| macOS | `~/pa-framework/` |
| Linux | `~/pa-framework/` o `/opt/pa-framework/` |

---

## ✅ Verificación

```bash
# Test que el hook funciona
python core/scripts/message_hook.py --stats

# Expected output:
# Session: abc123
# Messages: 5 captured
# Database: data/sessions.db ✓
```

---

## 🚨 Troubleshooting

### Windows: "python not found"

```powershell
# Usar py launcher
py core/scripts/message_hook.py --stats

# O añadir Python a PATH
$env:PATH += ";C:\Users\<user>\AppData\Local\Programs\Python\Python3x"
```

### macOS: "Permission denied"

```bash
chmod +x core/scripts/message_hook.py
```

### Linux: "Module not found"

```bash
# Asegurar sys.path
export PYTHONPATH="/path/to/pa-framework:$PYTHONPATH"
```

---

## 🔗 Integration Alternatives

### 1. Direct Python Import (recommended for skills)

```python
from core.scripts.message_hook import quick_capture

# En tu skill:
quick_capture("user", user_input)
quick_capture("assistant", ai_response)
```

### 2. Environment Variable

```bash
export PA_CAPTURE_HOOK='python /path/to/message_hook.py --capture'
# Luego cualquier CLI puede usar: $PA_CAPTURE_HOOK user "$text"
```

### 3. MCP Server (future)

```json
{
  "mcpServers": {
    "pa-memory": {
      "command": "python",
      "args": ["core/scripts/message_hook.py", "--mcp"]
    }
  }
}
```

---

## 📊 Captured Data

El hook guarda en SQLite:

| **Field** | **Type** | **Example** |
|-----------|----------|-------------|
| session_id | TEXT | `abc123-def456` |
| role | TEXT | `user`, `assistant`, `tool`, `system` |
| content | TEXT | Full message |
| channel | TEXT | `opencode`, `claude`, `gemini` |
| timestamp | DATETIME | `2026-04-18 21:12:36` |
| metadata | JSON | `{"model": "gpt-4o"}` |

---

## 🎓 Best Practices

1. **Session continuity**: Usa mismo `session_id` por proyecto
2. **Channel tagging**: Identifica el CLI usado (`opencode`, `claude`, etc.)
3. **Metadata**: Captura modelo usado, temperature, etc.
4. **Cross-platform**: Paths relativos al framework, nunca absolutos

---

## 📚 Related Docs

- `ROADMAP.md` - Dirección estratégica
- `CHANGELOG.md` - Historial de cambios
- `AGENTS.md` - Componentes del framework
- `core/scripts/message_hook.py` - Código fuente del hook
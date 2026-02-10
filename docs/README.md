# Personal Assistant Framework — Pre-Alpha 0.1.0

> Framework model-agnostic para gestionar asistentes AI personales con contexto local.

## 🚀 Quick Start

### Requisitos
- Python 3.11+
- Al menos un CLI de IA: [OpenCode](https://opencode.ai), [Gemini CLI](https://github.com/google-gemini/gemini-cli), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), o [Codex](https://openai.com/codex)

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git
cd Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha

# Ejecutar (la primera vez instala automáticamente)
# Windows:
pa.bat

# macOS/Linux:
chmod +x pa.sh
./pa.sh
```

El instalador te guiará por:
1. Verificación de dependencias
2. Selección de CLI por defecto
3. Sincronización de contexto inicial

### Uso Diario

```bash
pa.bat          # Abre el panel de control
```

Menú principal:
- **1. Sincronizar Contexto** — Alinea el contexto central con las herramientas
- **2. Iniciar Sesión AI** — Abre tu CLI de IA favorito con el contexto cargado
- **3. Configuración** — Estado del sistema, perfil, workspaces
- **4. Buscar Actualizaciones** — Verifica versión del framework

### Iniciar desde cualquier CLI

Si ya tienes una CLI de IA abierta, lee el archivo `Agents.md`:

```
Lee el archivo Agents.md e inicia la sesión de hoy.
```

Esto funciona con **cualquier CLI**: Gemini, Claude, OpenCode, Codex.

---

## 📁 Estructura

```
├── core/                  # Núcleo del framework
│   ├── .context/          # Conocimiento (MASTER.md, sessions, codebase)
│   ├── agents/            # Agentes AI definidos en .md
│   ├── skills/            # Habilidades modulares
│   └── scripts/           # Automatización Python
├── workspaces/            # Espacios por disciplina
├── docs/                  # Documentación
├── pa.bat / pa.sh         # Entry points
└── Agents.md              # Router para /init en cualquier CLI
```

## 📖 Más Información

- [Plan Pre-Alpha](PRE-ALPHA-PLAN.md) — Plan de implementación
- `core/agents/AGENTS.md` — Índice de agentes
- `core/skills/SKILLS.md` — Catálogo de skills
- `core/.context/navigation.md` — Mapa de navegación del contexto

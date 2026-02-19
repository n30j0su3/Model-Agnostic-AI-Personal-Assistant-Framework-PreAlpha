# Model-Agnostic AI Personal Assistant Framework

## Project Overview

The **Model-Agnostic AI Personal Assistant Framework** (Pre-Alpha 0.1.0) is a unified system designed to manage personal AI assistants with local context. It empowers users to own their data and leverage multiple AI tools (Gemini, Claude, OpenCode, Codex) seamlessly.

**Key Features:**
*   **Local Context:** All knowledge is stored in `.md` files under user control.
*   **Multi-Tool Workflow:** Supports simultaneous operation of major AI CLIs.
*   **Modular Architecture:** Extensible via **Agents** and **Skills**.
*   **Workspaces:** Pre-configured environments for different disciplines.
*   **Privacy-First:** All data stays local. No external telemetry.

## Building and Running

### Prerequisites
*   **Python:** 3.11+
*   **Git:** 2.30+ (optional)
*   **OS:** Windows 10/11, macOS 12+, or Linux.

### Key Commands

**Start the Framework:**
*   **Windows:** `pa.bat`
*   **macOS/Linux:** `./pa.sh`

**Menu Options:**
1. 🔄 Sincronizar Contexto
2. 🚀 Iniciar Sesión AI (OpenCode, Gemini, Claude, Codex)
3. ⚙️ Configuración (Estado, Perfil, Workspaces)
4. 🔄 Buscar Actualizaciones
0. 🚪 Salir

## Architecture

**Directory Structure:**
*   `core/.context/`: Central knowledge base (MASTER.md, sessions, codebase).
*   `core/agents/`: Specialized AI agents (FreakingJSON-PA, context-scout, session-manager).
*   `core/skills/`: Modular tools/capabilities (@pdf, @xlsx, @task-management).
*   `core/scripts/`: Python automation scripts (pa.py, install, sync).
*   `workspaces/`: Isolated domains for tasks.
*   `docs/`: Documentation.

## Key Components

### Core Agent: @FreakingJSON-PA
*   Manages sessions, context, and task delegation in production mode.
*   Delegates to subagents: @context-scout, @session-manager, @doc-writer.

### Core Skills
*   **@task-management:** Task tracking across workspaces.
*   **@pdf:** PDF processing.
*   **@xlsx:** Spreadsheet processing.
*   **@prompt-improvement:** Prompt optimization.

## Development Conventions

### Git Workflow
*   **Commit Messages:** In Spanish (`feat:`, `fix:`, `docs:`).
*   **Privacy:** NEVER commit real sessions or sensitive data.

### Critical Rules
*   All knowledge stored in `.md` files locally.
*   MVI Principle: Minimal Viable Information.
*   Framework-agnostic: Works with any AI CLI.

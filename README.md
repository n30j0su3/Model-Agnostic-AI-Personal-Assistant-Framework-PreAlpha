# Model-Agnostic AI Personal Assistant Framework v0.1.0-alpha

> "One Framework to rule them all, One Context to find them."
> "El Conocimiento verdadero trasciende a lo publico".

![Stage](https://img.shields.io/badge/stage-prealpha-red)
![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Agnostic](https://img.shields.io/badge/Model-Agnostic-orange)

## 🚀 Caracteristicas Principales

- 🤖 **Model-agnostic real**: compatible con OpenCode, Claude Code, Gemini CLI y Codex.
- 📁 **Contexto local**: el conocimiento vive en markdown dentro de `core/.context/`.
- 🧩 **Arquitectura modular**: agentes y skills desacoplados bajo `core/agents/` y `core/skills/`.
- 📝 **Trazabilidad**: sesiones diarias en `core/.context/sessions/`.
- 🔄 **Actualizacion integrada**: panel con opcion dedicada para buscar y aplicar updates.

## 🛠 Instalacion Rapida

1. **Clona el repositorio**:

```bash
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git
cd Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha
```

2. **Ejecuta el launcher**:

```bat
pa.bat
```

```bash
chmod +x pa.sh
./pa.sh
```

En la primera ejecucion, si no existe `core/.context/profile.md`, el launcher ejecuta automaticamente `core/scripts/install.py`.

## 🎛 Panel de Control

Menu principal:

1. 🔄 Sincronizar Contexto
2. 🚀 Iniciar Sesion AI
3. ⚙️ Configuracion
4. 🔄 Buscar Actualizaciones
0. 🚪 Salir

## 🧭 Comandos Utiles

```bash
# Panel (equivalente al launcher)
python core/scripts/pa.py

# Ver version runtime
python core/scripts/pa.py --version

# Sincronizar contexto manualmente
python core/scripts/sync-context.py

# Revisar actualizaciones
python core/scripts/update.py --check

# Forzar actualizacion
python core/scripts/update.py --force
```

## 📁 Estructura del Proyecto (PreAlpha)

```text
├── core/
│   ├── .context/          # MASTER, sesiones, codebase y contexto por CLI
│   ├── agents/            # Agente principal y subagentes
│   ├── skills/            # Skills modulares
│   └── scripts/           # Install, panel, sync, update
├── workspaces/            # Espacios por disciplina
├── docs/                  # Documentacion operativa
├── config/                # Branding y configuracion
├── pa.bat / pa.sh         # Launchers
├── Agents.md              # Router de inicializacion universal
├── GEMINI.md              # Contexto de apoyo para Gemini CLI
└── VERSION                # Fuente de verdad de version
```

## 🔒 Privacidad y Contexto Local

- Se versiona el contexto vital del framework para garantizar continuidad y reproducibilidad.
- Se evita subir secretos: `.env`, llaves (`*.key`, `*.pem`, `*.p12`) y `core/.context/env_vars.json`.
- Regla base: nunca comprometer credenciales reales en markdown o configuraciones.

## 🧪 Instalacion Completa (Paso a Paso)

1. Instala **Git** (recomendado) y **Python 3.11+**.
2. Clona el repo y entra a la carpeta.
3. Ejecuta `pa.bat` (Windows) o `./pa.sh` (macOS/Linux).
4. Configura preferencias en `core/.context/MASTER.md`.
5. Sincroniza contexto si hace falta:

```bash
python core/scripts/sync-context.py
```

6. Verifica que tengas archivos activos en:
   - `core/.context/profile.md`
   - `core/.context/sessions/`
   - `core/.context/codebase/`

## 🤖 Configuracion de LLMs (IA)

1. Crea cuentas en proveedores (OpenAI, Anthropic, Google, etc.).
2. Obtiene tus API keys.
3. Configura variables de entorno:

```bash
# macOS/Linux
export OPENAI_API_KEY="<TU_API_KEY>"
export ANTHROPIC_API_KEY="<TU_API_KEY>"
export GEMINI_API_KEY="<TU_API_KEY>"
```

```powershell
# Windows PowerShell
setx OPENAI_API_KEY "<TU_API_KEY>"
setx ANTHROPIC_API_KEY "<TU_API_KEY>"
setx GEMINI_API_KEY "<TU_API_KEY>"
```

4. Prueba tus CLIs (`opencode`, `claude`, `gemini`, `codex`).
5. Inicia el panel y entra por la opcion **2. Iniciar Sesion AI**.

## ❓ FAQ Basico

- **¿Necesito saber programar?** No, el flujo base esta pensado para uso guiado.
- **¿Donde vive mi conocimiento?** En `core/.context/`, bajo tu control.
- **¿Como actualizo el framework?** Opcion 4 del panel o `python core/scripts/update.py --check`.
- **¿Esto es gratis?** El framework es MIT; los proveedores de IA pueden tener costo.

## 📖 Documentacion

- `docs/README.md` (quick start tecnico)
- `docs/PRE-ALPHA-PLAN.md` (plan prealpha)
- `docs/PLAN_IMPLEMENTACION_REPO_PREALPHA.md` (plan de ejecucion del repo)
- `core/.context/navigation.md` (mapa de contexto)

## 🙏 Agradecimientos

Gracias a Dios por la Gracia, la Revelacion y el Discernimiento necesarios para llegar a la construccion del framework, a mi familia por su amor y paciencia, y al resto de mis seres amados y queridos (ellos saben quienes son, se los he dicho muchas veces).

Un agradecimiento especial a **[NetworkChuck](https://www.youtube.com/@NetworkChuck)** por inspirar la filosofia central de este proyecto (y gracias por tus oraciones también ;):

> *"I own my context. Nothing annoys me more than when AI tries to fence me in, give me vendor lock-in. No, I reject that."*

Su enfoque de soberania de datos y aprendizaje accesible fue fundamental para el diseno de este framework.

---
Hecho con ❤️ por el equipo de **Advanced Agentic Coding**.
Basado en las filosofías de **theNetworkChuck**.

## 🧭 Roadmap / Proximamente

Estas piezas fueron movidas al final para no contaminar el flujo de onboarding y quedaran habilitadas en futuras iteraciones:

- **Dev HQ vs Public Release**: flujo dedicado con comandos auxiliares (planeado).
- **Instaladores por SO**: wrappers `install.ps1` / `install.sh` (planeado).
- **Desinstalador oficial**: `uninstall.py` + guia de desinstalacion (planeado).
- **Dashboard interactivo**: `dashboard.html` standalone (planeado).

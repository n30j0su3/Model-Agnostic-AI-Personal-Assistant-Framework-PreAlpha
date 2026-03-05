# Model-Agnostic AI Personal Assistant Framework v0.1.3-prealpha

> "One Framework to rule them all, One Context to find them."
> "El Conocimiento verdadero trasciende a lo público".
> 
> **"True knowledge transcends to the public."**

[![Release](https://img.shields.io/badge/release-v0.1.0--alpha-blue)](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.3-prealpha)
[![Changelog](https://img.shields.io/badge/changelog-keep%20a%20changelog-green)](./CHANGELOG.md)
[![Instagram](https://img.shields.io/badge/Instagram-%40freakingjson-E4405F?logo=instagram&logoColor=white)](https://instagram.com/freakingjson)
[![Linktree](https://img.shields.io/badge/Linktree-@freakingjson-43E55C?logo=linktree&logoColor=white)](https://linktr.ee/freakingjson)
[![Blog](https://img.shields.io/badge/Blog-freakingjson.com-FFA500?logo=firefoxbrowser&logoColor=white)](https://freakingjson.com)
![Stage](https://img.shields.io/badge/stage-alpha-red)

![License](https://img.shields.io/badge/license-MIT-green)
![Agnostic](https://img.shields.io/badge/Model-Agnostic-orange)

---

## 📢 Latest Release

**v0.1.3-prealpha** - Workflow Standard: Proceso estructurado de 7 pasos
- Workflow Standard v1.0 con detección automática de complejidad
- Modo Express para tareas urgentes con transparencia total
- Configuración personalizable: `config/workflow-config.yaml`
- Integración visual en Dashboard SPA (tab Workflow)
- Case study: Dashboard SPA v2.0 como ejemplo del workflow
- 22 skills incluidas, 5 agentes desplegados
- Sistema de sync BASE/DEV/PROD completo

📄 [Ver Changelog](./CHANGELOG.md) | 🏷️ [Ver Releases](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases)

---

## 🚀 Características Principales

- 🤖 **Multi-Tool Workflow**: Trabaja con OpenCode, Claude Code, Gemini CLI y Codex simultáneamente.
- 📁 **Contexto Local**: Todo tu conocimiento reside en archivos `.md` bajo tu control.
- 🌐 **Multidisciplinario**: 6 Workspaces pre-configurados (Personal, Professional, Research, Content, Development, Homelab).
- 🛠 **Skills & Agents**: Sistema extensible basado en el estándar [Agent Skills](https://agentskills.io).
- 📝 **Trazabilidad Total**: Gestión de sesiones diarias con archivo histórico automático.
- ☁️ **Repositorio Inteligente**: Inicializa GitHub, Git local o modo Sandbox desde el instalador.
- 🌍 **Multi-idioma**: Selector ES/EN y preferencias guardadas en el contexto.
- 🎨 **Diseño Inteligente**: Integración nativa con `@ui-ux-pro-max` para interfaces profesionales.

## 📁 Estructura del Proyecto

```text
├── config/         # Configuración general
├── core/           # Núcleo del framework
│   ├── .context/   # Conocimiento central (MASTER.md)
│   ├── agents/     # Agentes especializados
│   ├── scripts/    # Automatización
│   └── skills/     # Habilidades modulares
├── docs/           # Documentación
├── logs/           # Logs del sistema
└── workspaces/     # ← Tus archivos de trabajo
```

## 🛠 Instalación Rápida

1. **Clonar o descargar el repo**:
   ```bash
   git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework.git
   ```
   Si usas el ZIP, extraelo y entra a la carpeta.
2. **Ejecutar el launcher**:
   ```bash
   ./pa.sh
   ```
   En Windows usa `pa.bat`. Si es la primera ejecucion, el launcher corre el instalador automaticamente.
   Si prefieres, puedes ejecutar `python scripts/install.py` manualmente.
   En la primera ejecucion, el instalador pregunta idioma y CLI por defecto.
   Si falta Python o Git, el launcher ofrece instalarlo (winget) o abrir la descarga.
   Si eliges OpenCode y falta Node.js, el instalador ofrece instalarlo.
3. **Configurar tu perfil**:
   Edita `.context/MASTER.md` con tus preferencias.
4. **Sincronizar**:
   ```bash
   python scripts/sync-context.py
   ```

## 🎛 Panel de Control (Opcional)

Si prefieres gestionar el framework desde un unico menu interactivo:

```bash
python scripts/pa.py
```

Atajos opcionales:

```bash
./pa.sh
```

```bat
pa.bat
```

Desde ahi puedes sincronizar contexto, ajustar preferencias, activar orquestacion
multi-modelo y lanzar tu sesion AI sin ejecutar scripts sueltos.

## Dev HQ vs Public Release

Este repo funciona como Dev HQ (privado): contiene backlog real, sesiones y trazabilidad completa.
La publicacion al repo publico se hace con un flujo separado y sanitizado.

Reglas clave:
- `origin` = repo privado (dev)
- `upstream` = repo publico (release)
- `main` = desarrollo privado
- `public-release` = publicacion sanitizada

Comandos:
- Iniciar sesion de features (Dev HQ):
  - Windows: `dev.bat`
  - macOS/Linux: `./dev.sh`
- Publicar a repo publico (sanitizado):
  - `python scripts/publish-release.py --push`

## 🧰 Pre-requisitos (Hardware y Software)

- **Hardware minimo**: CPU 4 nucleos, 8 GB RAM, 2 GB libres en disco.
- **Hardware recomendado**: CPU 8 nucleos, 16 GB RAM, SSD.
- **GPU (opcional)**: Recomendada si usaras modelos locales o flujos pesados.
- **Sistema operativo**: Windows 10/11, macOS 12+ o Linux moderno.
- **Software base**: Git 2.30+, Python 3.11+ y un editor (VS Code u otro).
- **Cuentas IA**: Acceso a proveedores como OpenAI, Anthropic o Google si usaras sus APIs.

## 🧭 Instalación Completa (Para Dummies)

1. **Instala Git** desde https://git-scm.com y reinicia la terminal.
2. **Instala Python 3.11+** desde https://www.python.org y confirma con `python --version`.
3. **Crea una carpeta** para el proyecto y abre una terminal dentro.
4. **Clona el repo**:
   ```bash
   git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework.git
   ```
5. **Entra a la carpeta**:
   ```bash
   cd Model-Agnostic-AI-Personal-Assistant-Framework
   ```
6. **Configura tu perfil** editando `core/.context/MASTER.md`.
7. **Sincroniza el contexto**:
   ```bash
   python core/scripts/sync-context.py
   ```
8. **Verifica** que se generaron archivos de contexto en `core/.context/` y `core/.context/sessions/`.
9. **Comienza a trabajar** en tu carpeta `workspaces/` (allí van tus archivos personales).
9. **Listo**: ya puedes iniciar sesiones y activar skills.

## 🤖 Instalación de LLMs (IA) Paso a Paso

1. **Crea cuentas** en los proveedores que vayas a usar (OpenAI, Anthropic, Google, etc.).
2. **Obtén tus API Keys** desde el panel de cada proveedor.
3. **Instala las CLIs** oficiales (OpenCode, Claude Code, Gemini CLI, Codex) siguiendo sus docs.
4. **Configura las variables de entorno** con tus claves.
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
5. **Prueba cada CLI** con un comando simple (por ejemplo `--version` o un prompt corto).
6. **Vincula el contexto** ejecutando `python scripts/sync-context.py` si aun no lo hiciste.
7. **Valida la configuracion LLM** con el instalador:
   ```bash
   python scripts/install.py --llm
   ```

### 🧠 Modelos locales (Opcional)

- **Ollama (Windows/macOS/Linux)**
  1. Instala desde https://ollama.com
  2. Descarga un modelo:
     ```bash
     ollama pull llama3
     ```
  3. Prueba el modelo:
     ```bash
     ollama run llama3
     ```
  4. Configura tu herramienta LLM para apuntar al endpoint local que expone Ollama.

- **LM Studio (Windows/macOS/Linux)**
  1. Instala desde https://lmstudio.ai
  2. Descarga un modelo desde la app.
  3. Activa el servidor local desde la interfaz y usa el endpoint que te muestre la app.

## 🧩 Instalador Todo-en-Uno (Comando Unico)

```powershell
# Windows PowerShell
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework.git; cd Model-Agnostic-AI-Personal-Assistant-Framework; python scripts/install.py
```

```bash
# macOS/Linux
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework.git && cd Model-Agnostic-AI-Personal-Assistant-Framework && python3 scripts/install.py
```

Luego edita `.context/MASTER.md` con tus preferencias personales.

## 🐍 Instalador Python (Multiplataforma)

- **Windows**:
  ```powershell
  python scripts/install.py
  # o
  py -3 scripts/install.py
  ```
- **macOS/Linux**:
  ```bash
  python3 scripts/install.py
  ```

Para validar LLMs agrega `--llm`.

## 🧪 Instalador por SO (Opcional)

- **Windows PowerShell**:
  ```powershell
  .\scripts\install.ps1
  ```
- **macOS/Linux**:
  ```bash
  bash scripts/install.sh
  ```

## 🛠 Troubleshooting Windows (PowerShell)

Si PowerShell bloquea `opencode` con un error de politica de ejecucion, ejecuta:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

## 🧹 Desinstalacion (Opcional)

Si necesitas remover el framework de forma segura:

```bash
python scripts/uninstall.py
```

Guia completa: `docs/uninstall.mdx`

## ❓ FAQ Basico

- **¿Necesito saber programar?** No. Esta guia esta pensada para principiantes.
- **¿Donde vive mi conocimiento?** Tus archivos van en `workspaces/`. La configuración del framework está en `core/.context/`.
- **¿Que pasa si no tengo API key?** Puedes usar el framework, pero sin ejecutar modelos remotos.
- **¿Como actualizo el framework?** Con Git: `git pull`. Con ZIP: copia `core/.context/` y `workspaces/` (y opcionalmente `docs/` y `config/`) a la nueva versión.
- **¿Esto es gratis?** El framework es MIT, pero los proveedores de IA pueden cobrar por uso.

## 🙏 Agradecimientos

Gracias a Dios por la Gracia, la Revelacion y el Discernimiento necesarios para llegar a la construccion del framework, a mi familia por su amor y paciencia, y al resto de mis seres amados y queridos (ellos saben quienes son, se los he dicho muchas veces).

Un agradecimiento especial a **[NetworkChuck](https://www.youtube.com/@NetworkChuck)** por inspirar la filosofia central de este proyecto (y gracias por tus oraciones también ;):

> *"I own my context. Nothing annoys me more than when AI tries to fence me in, give me vendor lock-in. No, I reject that."*

Su enfoque de soberania de datos y aprendizaje accesible fue fundamental para el diseno de este framework.

## 📖 Documentación

La documentación completa está disponible en la carpeta `docs/`. Sigue el estándar de Mintlify para una experiencia de lectura superior.

### 📊 Dashboard Interactivo

El archivo `dashboard.html` es una interfaz visual standalone que te permite:

- Explorar el framework (introduccion, primeros pasos, filosofia)
- Navegar Workspaces (Personal, Professional, Research, Content, Development)
- Conocer Agentes y Skills disponibles
- Entender el Ciclo Diario de trabajo

Para usarlo, abre el archivo en tu navegador:

```bash
open dashboard.html        # macOS
start dashboard.html       # Windows
xdg-open dashboard.html    # Linux
```

No requiere servidor ni dependencias externas.

---

## 🔗 Conecta con FreakingJSON

- 📸 **Instagram**: [@freakingjson](https://instagram.com/freakingjson)
- 🌐 **Todas las redes**: [linktr.ee/freakingjson](https://linktr.ee/freakingjson)
- 📝 **Blog Tech & Homelab**: [freakingjson.com](https://freakingjson.com)
- ☕ **Apoya el proyecto**: [buymeacoffee.com/freakingjson](https://buymeacoffee.com/freakingjson)

---

Hecho con ❤️ por **FreakingJSON**.

> **"El conocimiento verdadero trasciende a lo público."**
> 
> **"True knowledge transcends to the public."**
> 
> *I own my context. I am FreakingJSON.*

Basado en las filosofías de **theNetworkChuck**.

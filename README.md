# Model-Agnostic AI Personal Assistant Framework v0.1.0-alpha

> "Tu Asistente AI Personal. Tu Conocimiento. Tu Control."

[![Release](https://img.shields.io/badge/release-v0.1.0--alpha-blue)](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.0-alpha)
[![Changelog](https://img.shields.io/badge/changelog-keep%20a%20changelog-green)](./CHANGELOG.md)
![Stage](https://img.shields.io/badge/stage-alpha-red)
![License](https://img.shields.io/badge/license-MIT-green)

[🇺🇸 English Version](./README_en.md)

---

## 🎯 Objetivo y Filosofía

**¿Qué es esto?**

Un asistente de inteligencia artificial que vive en **tu computadora**, no en servidores de terceros. Tus conversaciones, documentos y conocimiento permanecen en archivos locales que **tú controlas completamente**.

**La filosofía es simple:**

- 📍 **Local-first**: Todo funciona en tu PC, sin depender de internet constantemente
- 🔐 **Tu control**: Tu información nunca se vende ni se usa para entrenar modelos ajenos
- 🔄 **Sin vendor lock-in**: Funciona con OpenAI, Claude, Gemini, o modelos locales. Tú eliges.

> *"El conocimiento verdadero trasciende a lo público, pero debe permanecer bajo tu control."*

---

## ✨ Características Principales

| Feature | Descripción |
|---------|-------------|
| 🤖 **Multi-IA** | Compatible con OpenCode, Claude Code, Gemini CLI y más |
| 📁 **Tus archivos** | Todo tu conocimiento en archivos `.md` que puedes editar, mover o respaldar |
| 🛠️ **15 Skills incluidas** | Trabaja con Excel, PDF, Word, Markdown, tareas y más |
| 🌍 **Bilingüe** | Interfaz y documentación en Español e Inglés |
| 📅 **Sesiones diarias** | El asistente recuerda contexto entre conversaciones |
| ⚡ **Fácil de usar** | Instalación en 3 pasos, sin configuraciones complejas |

---

## 📁 Estructura Simple

```
📂 Tu carpeta del asistente/
├── 📄 Conocimiento/           # Archivos de contexto (.md)
├── 🤖 Agentes/                # Configuración de asistentes
├── 🛠️ Skills/                 # Herramientas (Excel, PDF, etc.)
├── 💼 Workspaces/             # Espacios de trabajo por proyecto
└── 📅 Sessions/               # Historial de conversaciones
```

**Todo son archivos de texto.** Puedes abrirlos, editarlos, respaldarlos o sincronizarlos con tu sistema favorito (Google Drive, Dropbox, etc.).

---

## ⚡ Quick Start (Windows)

> 💡 **También disponible para Mac y Linux** - ver notas al final.

### Paso 1: Descargar
```powershell
# Opción A: Con Git (recomendado para actualizaciones)
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git

# Opción B: Descargar ZIP desde la página de Releases arriba ↑
```

### Paso 2: Ejecutar
```powershell
# Entra a la carpeta y ejecuta:
cd Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha
pa.bat
```

### Paso 3: Configurar
El instalador te hará 3 preguntas simples:
1. ¿Qué idioma prefieres? (Español/English)
2. ¿Qué herramienta de IA usarás principalmente? (OpenCode, Claude, etc.)
3. ¿Cómo te llamas? (para personalizar el asistente)

### ¡Listo! 🎉

Tu asistente está configurado. Ahora puedes:
- Escribir `pa.bat` para iniciar una sesión
- Editar archivos en la carpeta `workspaces/` para darle contexto
- Pedirle ayuda con documentos, datos, o tareas diarias

---

## 📋 Pre-requisitos

### Hardware
| Mínimo | Recomendado |
|--------|-------------|
| 4 núcleos CPU | 8 núcleos CPU |
| 8 GB RAM | 16 GB RAM |
| 2 GB espacio libre | 5 GB espacio libre |

### Software
- **Windows 10/11** (también disponible para macOS 12+ y Linux moderno)
- **Python 3.11+** *(se instala automáticamente si falta)*
- **Git** *(opcional, solo para actualizaciones)*

### Opcional: Cuentas de IA
Para usar modelos avanzados (GPT-4, Claude, etc.) necesitarás:
- Una cuenta gratuita en el proveedor que elijas
- API key (te lo explicamos cómo obtenerlo en la documentación completa)

> 💡 **Sin API key también funciona** - puedes usar modelos locales gratuitos como Ollama.

---

## ❓ FAQ Básico

**¿Necesito saber programar?**
→ **No.** Esta guía está pensada para cualquier persona. Si sabes usar una terminal básica, es suficiente.

**¿Es gratis?**
→ **El framework es 100% gratis** (licencia MIT). Algunos proveedores de IA (OpenAI, etc.) pueden cobrar por uso intensivo, pero hay opciones gratuitas disponibles.

**¿Mis datos son míos?**
→ **Sí, completamente.** Todo queda en tu computadora en archivos de texto. No enviamos tu información a servidores externos sin tu permiso explícito.

**¿Puedo usarlo sin internet?**
→ **Parcialmente.** El framework funciona offline, pero necesitarás internet para consultar modelos de IA en la nube. También puedes instalar modelos locales (como Ollama) para trabajo 100% offline.

**¿Cómo actualizo el framework?**
→ Si usaste Git: `git pull`. Si descargaste ZIP: descarga la nueva versión y copia tu carpeta `.context/` (tu conocimiento) a la nueva instalación.

**¿Qué pasa si algo no funciona?**
→ Revisa nuestra documentación completa o abre un issue en GitHub. La comunidad te ayuda.

---

## 🙏 Agradecimientos

Gracias a Dios por la Gracia, la Revelación y el Discernimiento necesarios para construir este framework.

Un agradecimiento especial a **[NetworkChuck](https://www.youtube.com/@NetworkChuck)** por inspirar la filosofía central de este proyecto:

> *"I own my context. Nothing annoys me more than when AI tries to fence me in, give me vendor lock-in. No, I reject that."*

Su enfoque de soberanía de datos y aprendizaje accesible fue fundamental para el diseño de este framework.

---

## 🔗 Documentación Completa

**¿Eres desarrollador o necesitas información técnica detallada?**

👉 [Ver documentación técnica completa aquí](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework/blob/main/README-FULL.md)

Incluye:
- Instalación avanzada por sistema operativo
- Configuración de múltiples modelos de IA
- Guía de desarrollo de skills personalizadas
- Arquitectura técnica del framework
- Troubleshooting detallado

---

## 🍎 🐧 Nota para usuarios Mac y Linux

Este framework también funciona en **macOS 12+** y **Linux moderno** (Ubuntu 20.04+, Fedora, etc.).

**Comandos equivalentes:**
```bash
# En lugar de pa.bat, usa:
./pa.sh

# Instalación:
python3 scripts/install.py
```

La estructura y funcionamiento son idénticos. Solo cambian las extensiones de archivos de script.

---

Hecho con ❤️ por **FreakingJSON**.

> *"I own my context. I am FreakingJSON."*

# Model-Agnostic AI Personal Assistant Framework v0.1.4-prealpha (Technical Documentation)

> **Documentación Técnica Completa para Desarrolladores**

[![Release](https://img.shields.io/badge/release-v0.1.4--prealpha-blue)](https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases/tag/v0.1.4-prealpha)
[![Changelog](https://img.shields.io/badge/changelog-keep%20a%20changelog-green)](./CHANGELOG.md)
![Stage](https://img.shields.io/badge/stage-alpha-red)

![License](https://img.shields.io/badge/license-MIT-green)
![Agnostic](https://img.shields.io/badge/Model-Agnostic-orange)

---

## 👥 Versión para Usuarios

**Esta es la documentación técnica completa para desarrolladores.**

👉 [Ver versión simplificada para usuarios aquí](./README.md)  
👉 [View simplified user version (English)](./README_en.md)

---

## 📋 Tabla de Contenidos

1. [Arquitectura del Framework](#arquitectura)
2. [Instalación Avanzada](#instalacion-avanzada)
3. [Configuración de Modelos de IA](#configuracion-modelos)
4. [Desarrollo de Skills](#desarrollo-skills)
5. [Estructura del Proyecto](#estructura)
6. [Dashboard SPA](#dashboard-spa)
7. [Knowledge Base](#knowledge-base)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Arquitectura del Framework {#arquitectura}

### Filosofía de Diseño

El framework está construido sobre principios de:
- **Local-first**: Todo el procesamiento ocurre en tu máquina
- **Privacy-by-design**: Tus datos nunca salen de tu control
- **Model-agnostic**: Funciona con cualquier proveedor de IA
- **Extensible**: Sistema de skills modular

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                    PA Framework Core                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Context    │  │   Skills     │  │   Agents     │      │
│  │   Engine     │  │   Registry   │  │   System     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    Interface Layer                          │
│         (OpenCode, Claude Code, Gemini CLI, etc.)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Instalación Avanzada {#instalacion-avanzada}

### Requisitos del Sistema

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| Python | 3.9+ | 3.11+ |
| RAM | 4 GB | 8 GB |
| Disco | 500 MB | 2 GB (con workspaces) |
| OS | Windows 10, macOS 12, Ubuntu 20.04 | Última versión estable |

### Instalación por Sistema Operativo

#### Windows (PowerShell como Administrador)

```powershell
# 1. Clonar repositorio
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git

# 2. Ejecutar instalador
.\install.ps1

# 3. Configurar variables de entorno (opcional)
[Environment]::SetEnvironmentVariable("PA_FRAMEWORK_PATH", "C:\ruta\al\framework", "User")
```

#### macOS / Linux (Terminal)

```bash
# 1. Clonar repositorio
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git

# 2. Ejecutar instalador
chmod +x install.sh
./install.sh

# 3. Agregar al PATH (agregar a ~/.bashrc o ~/.zshrc)
export PATH="$PATH:/ruta/al/framework"
```

---

## 🤖 Configuración de Modelos de IA {#configuracion-modelos}

### OpenCode

Configuración en `~/.opencode/config.json`:

```json
{
  "mcp": {
    "context7": {
      "type": "local",
      "command": ["npx", "-y", "@upstash/context7-mcp"],
      "enabled": true
    }
  },
  "agent": "FreakingJSON-PA"
}
```

### Claude Code

```bash
# Configurar Claude Code para usar el framework
claude config set mcpServers.context7 "npx -y @upstash/context7-mcp"
```

### Gemini CLI

```bash
# Configurar contexto del framework
gemini config context path/to/framework
```

---

## 🛠️ Desarrollo de Skills {#desarrollo-skills}

### Estructura de una Skill

```
core/skills/@mi-skill/
├── SKILL.md              # Documentación y metadatos
├── README.md             # Guía de uso
├── src/                  # Código fuente
│   ├── __init__.py
│   └── main.py
├── tests/                # Tests unitarios
└── examples/             # Ejemplos de uso
```

### Template SKILL.md

```yaml
---
skill:
  name: "@mi-skill"
  version: "1.0.0"
  description: "Descripción de la skill"
  author: "Tu Nombre"
  tags: ["categoría", "tag2"]
  
inputs:
  - name: "parametro1"
    type: "string"
    required: true
    description: "Descripción del parámetro"

outputs:
  - name: "resultado"
    type: "object"
    description: "Resultado de la operación"
---

# @mi-skill

## Descripción

Documentación detallada de la skill...

## Uso

```python
# Ejemplo de uso
from skills.mi_skill import main
result = main.procesar(parametro1="valor")
```

## API Reference

### Funciones Principales

| Función | Descripción | Parámetros |
|---------|-------------|------------|
| `procesar()` | Procesa los datos | `parametro1` (str) |
```

---

## 📁 Estructura del Proyecto {#estructura}

```text
Model-Agnostic-AI-Personal-Assistant-Framework/
│
├── 📂 core/                          # Núcleo del framework
│   ├── 📂 .context/                  # Conocimiento central
│   │   ├── MASTER.md                 # Configuración global
│   │   ├── navigation.md             # Mapa de navegación
│   │   ├── sessions/                 # Historial de sesiones
│   │   └── knowledge/                # Base de conocimiento
│   │
│   ├── 📂 agents/                    # Agentes del sistema
│   │   ├── pa-assistant.md           # Agente principal
│   │   ├── AGENTS.md                 # Registro de agentes
│   │   └── subagents/                # Subagentes especializados
│   │
│   ├── 📂 scripts/                   # Scripts de automatización
│   │   ├── session-start.py          # Inicio de sesión
│   │   ├── knowledge-indexer.py      # Indexación de conocimiento
│   │   ├── interaction-logger.py     # Logging de interacciones
│   │   └── generate-dashboard-data.py # Generador de dashboard
│   │
│   ├── 📂 skills/                    # Skills del framework
│   │   ├── @skill-name/              # Skill específica
│   │   └── _local/                   # Skills locales del usuario
│   │
│   └── 📂 templates/                 # Plantillas
│       └── skill-template/           # Template para nuevas skills
│
├── 📂 workspaces/                    # Espacios de trabajo
│   ├── personal/                     # Proyectos personales
│   ├── professional/                 # Proyectos profesionales
│   ├── research/                     # Investigación
│   ├── content/                      # Creación de contenido
│   ├── development/                  # Desarrollo de software
│   └── homelab/                      # Homelab y experimentos
│
├── 📂 docs/                          # Documentación
│   ├── README-TECNICO.md             # Esta documentación
│   ├── WORKFLOW-STANDARD.md          # Proceso de trabajo
│   ├── PHILOSOPHY.md                 # Principios del framework
│   └── CHANGELOG.md                  # Historial de cambios
│
├── dashboard.html                    # Dashboard SPA v2.0
├── dashboard-data.js                 # Datos embebidos del dashboard
├── pa.bat / pa.sh                    # Entry points
├── install.py                        # Instalador
└── VERSION                           # Versión actual
```

---

## 📊 Dashboard SPA {#dashboard-spa}

### Características

- **SPA (Single Page Application)**: Sin servidor requerido
- **CORS-free**: Funciona con protocolo `file://`
- **Datos embebidos**: No requiere backend
- **Visualizaciones**: Charts, métricas, timelines
- **Estado persistente**: LocalStorage para preferencias

### Uso

```bash
# Abrir directamente en navegador
open dashboard.html

# O servir localmente (opcional)
python -m http.server 8000
```

### Componentes

| Componente | Descripción |
|------------|-------------|
| Overview | Estado general del framework |
| Workflows | Progreso de workflows activos |
| Skills | Catálogo de skills disponibles |
| Agents | Agente activo y subagentes |
| Sessions | Historial de sesiones |
| Vitals | Salud del sistema |

---

## 🧠 Knowledge Base {#knowledge-base}

### Sistema de Indexación

El framework incluye un sistema de knowledge base que indexa:

- **Patrones de uso**: Cómo interactúas con el framework
- **Skills más usadas**: Frecuencia de uso de cada skill
- **Sesiones**: Historial completo con metadatos
- **Insights**: Tendencias y recomendaciones

### Scripts del Sistema

| Script | Función |
|--------|---------|
| `knowledge-indexer.py` | Genera índices de patrones y tendencias |
| `interaction-logger.py` | Registra cada interacción estructurada |
| `optimization-reporter.py` | Genera reportes de optimización |
| `generate-dashboard-indexes.py` | Actualiza índices para el dashboard |

### Ejecución Manual

```bash
# Indexar patrones de conocimiento
python core/scripts/knowledge-indexer.py

# Generar reporte de optimización
python core/scripts/optimization-reporter.py

# Actualizar índices del dashboard
python core/scripts/generate-dashboard-indexes.py
```

---

## 🔧 Troubleshooting {#troubleshooting}

### Problemas Comunes

#### Error: "No se encuentra el contexto"

**Causa**: El directorio `.context/` no está inicializado.

**Solución**:
```bash
python core/scripts/session-start.py
```

#### Error: "Skill no encontrada"

**Causa**: La skill no está registrada en `core/skills/`.

**Solución**:
```bash
# Verificar estructura
dir core/skills/@nombre-skill/SKILL.md

# Re-indexar skills
python core/scripts/session-start.py --reindex
```

#### Dashboard no carga datos

**Causa**: `dashboard-data.js` no está actualizado.

**Solución**:
```bash
# Regenerar datos del dashboard
python core/scripts/generate-dashboard-data.py
```

### Logs y Debugging

| Ubicación | Contenido |
|-----------|-----------|
| `logs/session-*.log` | Logs de sesiones |
| `logs/error-*.log` | Errores del sistema |
| `.context/debug/` | Información de debugging |

### Soporte

- 📸 **Instagram**: [@freakingjson](https://instagram.com/freakingjson)
- 🌐 **Linktree**: [linktr.ee/freakingjson](https://linktr.ee/freakingjson)
- 📝 **Blog**: [freakingjson.com](https://freakingjson.com)

---

## 📄 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](./LICENSE).

Copyright (c) 2025 FreakingJSON

---

Hecho con ❤️ por **FreakingJSON**.

> *"I own my context. I am FreakingJSON."*

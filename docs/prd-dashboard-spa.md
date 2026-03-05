---
title: PRD - Dashboard SPA FreakingJSON Framework
author: FreakingJSON-PA Framework
status: Draft
version: 1.0.0
date: 2026-03-04
---

# Product Requirements Document
## Dashboard SPA - FreakingJSON Personal Assistant Framework

---

## 1. OVERVIEW

### Problem Statement
Los usuarios nuevos del framework necesitan una interfaz visual intuitiva para:
- Entender el propósito y filosofía del framework
- Explorar sus sesiones históricas de forma visual (tipo ChatGPT)
- Descubrir skills, agentes y recursos disponibles
- Acceder rápidamente a funcionalidades (pa.bat, workspaces)
- Navegar sin depender exclusivamente de CLI

### Proposed Solution
Un Dashboard SPA (Single Page Application) como archivo HTML único que funcione offline, con:
- Onboarding interactivo con filosofía del framework
- Vista tipo ChatGPT para explorar sesiones históricas
- Chat UI en modo lectura (visualización de sesiones)
- Sección Framework Internals (skills, agentes, codebase)
- Accesos rápidos y about con redes sociales

### Success Metrics
- Usuario nuevo entiende el framework en <5 minutos
- Navegación a cualquier sesión histórica en <3 clicks
- Zero dependencias externas (funciona offline)
- Tamaño <1MB para carga rápida

---

## 2. GOALS & NON-GOALS

### Goals
- [ ] Dashboard HTML único, sin dependencias de build
- [ ] Onboarding con filosofía y guía de inicio
- [ ] Navegación tipo ChatGPT/DeepSeek para sesiones
- [ ] Chat UI modo lectura con banner explicativo
- [ ] Framework Internals: skills, agentes, codebase
- [ ] Búsqueda full-text integrada
- [ ] Accesos rápidos a pa.bat/sh
- [ ] About Us con redes sociales y donaciones

### Non-Goals
- [ ] Chat funcional con conexión real-time (futuro FE-004)
- [ ] Backend server requerido
- [ ] Autenticación de usuarios
- [ ] Sincronización cloud

---

## 3. USERS & CONTEXT

### Primary Users
- **Usuarios nuevos**: Nunca usaron CLI, necesitan GUI familiar
- **Usuarios ocasionales**: Prefieren navegar sesiones visualmente
- **Usuarios avanzados**: Usan dashboard como referencia rápida

### Usage Context
- Abierto desde pa.bat/sh opción "Abrir Dashboard"
- Ejecutado directamente haciendo doble-click
- Servido localmente con `python -m http.server`

### Constraints
- Debe funcionar completamente offline
- No frameworks pesados (React/Vue) - vanilla JS
- Compatible con Chrome, Firefox, Safari, Edge
- Responsive: desktop + tablet

---

## 4. REQUIREMENTS

### User Stories

#### US-001: Onboarding
```
Como usuario nuevo
Quiero ver la filosofía y guía de inicio al abrir el dashboard
Para entender qué es el framework y cómo empezar
```
**Acceptance Criteria:**
- Sección "Objetivo y Filosofía" visible en Home
- Explicación de los 4 pilares (local-first, privacy-first, MVI, multi-CLI)
- Guía paso a paso: "Cómo empezar"
- Enlace a guía de migración de archivos

#### US-002: Navegación Sesiones tipo ChatGPT
```
Como usuario
Quiero una navegación lateral tipo ChatGPT/DeepSeek
Para explorar mis sesiones históricas organizadas por fecha
```
**Acceptance Criteria:**
- Sidebar con sesiones agrupadas por fecha (Hoy, Ayer, Esta semana, Mes)
- Preview de cada sesión con título y primeras líneas
- Filtros por etiquetas/topics
- Búsqueda en tiempo real

#### US-003: Chat UI Modo Lectura
```
Como usuario
Quiero ver el contenido de una sesión en formato chat
Para leer la conversación de forma familiar
```
**Acceptance Criteria:**
- Vista tipo chat con mensajes del agente y usuario
- Banner amarillo en la parte superior: "MODO LECTURA - Explora sesiones históricas aquí. La integración completa con CLI vendrá en una futura actualización."
- Navegación entre sesiones sin recargar

#### US-004: Framework Internals
```
Como usuario curioso
Quiero ver información detallada de skills, agentes y codebase
Para entender cómo funciona el framework internamente
```
**Acceptance Criteria:**
- Sección/Tab "Framework Internals"
- Lista de skills con descripciones
- Lista de agentes con responsabilidades
- Mapa de codebase/estructura de directorios

#### US-005: Accesos Rápidos
```
Como usuario
Quiero botones para ejecutar pa.bat/sh directamente
Para no tener que navegar al directorio
```
**Acceptance Criteria:**
- Botón "Iniciar pa.bat" (Windows)
- Botón "Iniciar pa.sh" (Mac/Linux)
- Botón "Abrir Workspaces"
- Botón "Ver Documentación"

#### US-006: About Us Completo
```
Como usuario
Quiero ver información del proyecto, redes y cómo apoyar
Para conectar con la comunidad y contribuir
```
**Acceptance Criteria:**
- Filosofía del framework
- Enlaces a redes sociales (extraídos de README-simple.md)
- Link a linktr.ee/freakingjson
- Botones de donación/apoyo
- Agradecimientos

### Functional Requirements

#### FR-001: Home/Onboarding
- Hero section con logo y tagline
- Objetivo y Filosofía del framework
- Cards de características (Rápido, Privado, Personal, Analytics)
- Guía "Cómo empezar" (3 pasos)
- Guía de migración de archivos a workspaces
- Accesos rápidos grandes y visibles

#### FR-002: Chat UI
- Layout tipo ChatGPT: sidebar izquierda + chat derecha
- Sidebar con lista de sesiones agrupadas por fecha
- Filtros por tipo (features, bugfix, research)
- Búsqueda con autocompletado
- Área de chat con mensajes estilizados
- Banner MODO LECTURA fijo en top
- Navegación fluida entre sesiones

#### FR-003: Framework Internals
- Tabs: Skills | Agents | Codebase | Knowledge Base
- Skills: grid de tarjetas con nombre, descripción, uso
- Agents: lista con responsabilidades y cuándo usarlos
- Codebase: árbol de directorios interactivo
- Stats: métricas del framework

#### FR-004: Search
- Barra de búsqueda global
- Búsqueda en sesiones, skills, codebase
- Autocompletado basado en trigramas
- Resultados con highlighting
- Filtros por tipo de contenido

#### FR-005: Responsive
- Desktop: sidebar visible + chat area
- Tablet: sidebar colapsable
- Mobile: navegación por tabs

### Non-Functional Requirements

#### NFR-001: Performance
- First paint <2s
- Tamaño total <1MB
- Lazy loading de sesiones
- Virtual scrolling para listas largas

#### NFR-002: Offline
- Funciona 100% sin internet
- No CDN externo (Tailwind via CDN inline o local)
- Chart.js inline o vendored

#### NFR-003: Compatibility
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

---

## 5. DESIGN & TECH

### User Flows

#### Flow 1: Usuario nuevo descubre el framework
```
Abre dashboard.html
    ↓
Ve Home con filosofía
    ↓
Lee "Cómo empezar"
    ↓
Hace click en "Iniciar pa.bat"
    ↓
Framework se ejecuta en terminal
```

#### Flow 2: Usuario explora sesiones históricas
```
Abre dashboard.html
    ↓
Navega a Chat UI
    ↓
Ve sidebar con sesiones
    ↓
Hace click en sesión de ayer
    ↓
Lee conversación en formato chat
    ↓
Usa filtros para encontrar sesión específica
```

#### Flow 3: Usuario busca información
```
En cualquier vista
    ↓
Escribe en barra de búsqueda
    ↓
Ve resultados con autocompletado
    ↓
Selecciona resultado
    ↓
Navega a contenido
```

### Technical Stack

**Core:**
- HTML5 semantic
- Vanilla JavaScript (ES2020)
- Tailwind CSS 3.4 (CDN inline para offline)

**Charts:**
- Chart.js 4.x (CDN inline para offline)

**Data:**
- sessions-index.json (cargado vía fetch)
- search-index.db (vía sql.js para búsqueda en cliente)

**Icons:**
- Heroicons (inline SVG)

### Wireframes

#### Home View
```
┌─────────────────────────────────────────────────────────────┐
│  [LOGO] FreakingJSON Framework v0.1.2        [🔍] [⚙️] [👤] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ "Tu Asistente AI Personal. Tu Conocimiento.          │ │
│  │  Tu Control."                                         │ │
│  │                                                       │ │
│  │ [⚡ Iniciar Framework] [📁 Workspaces] [📚 Docs]      │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ OBJETIVO Y FILOSOFÍA                                  │ │
│  │ Este framework te permite gestionar tu conocimiento...│ │
│  │ • Local-first • Privacy-first • MVI • Multi-CLI      │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐    │
│  │ CÓMO EMPEZAR  │ │ MIGRAR ARCHS  │ │ EJEMPLOS      │    │
│  │ 1. Ejecutar   │ │ 1. Crear WS   │ │ Ver demos     │    │
│  │ 2. Configurar │ │ 2. Copiar     │ │               │    │
│  │ 3. Usar       │ │ 3. Organizar  │ │               │    │
│  └───────────────┘ └───────────────┘ └───────────────┘    │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ FRAMEWORK INTERNALS                                   │ │
│  │ [Skills: 22] [Agents: 5] [Sessions: 45] [Projects: 8]│ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Chat UI View
```
┌─────────────────────────────────────────────────────────────┐
│  [≡]  CHAT - MODO LECTURA                        [⚙️] [👤] │
├────────────────┬────────────────────────────────────────────┤
│ NAVEGACIÓN     │ CONVERSACIÓN                               │
│                │                                            │
│ 🔍 Buscar...   │ ┌────────────────────────────────────────┐│
│                │ │ ⚠️ MODO LECTURA                          ││
│ 📅 HOY         │ │ Explora sesiones históricas aquí.      ││
│ ├─ Release...  │ │ Integración completa: Próximamente     ││
│ 📅 AYER        │ └────────────────────────────────────────┘│
│ ├─ Knowledge   │                                            │
│ 📅 MARZO       │ 🤖 FreakingJSON-PA                         │
│ ├─ Investigac. │ │ Hola! Explora tus sesiones...           ││
│ ├─ Skills      │                                            │
│ └─ +5 más...   │ 👤 Usuario                                 │
│                │ │ [Selecciona sesión]                     ││
│ 🏷️ ETIQUETAS   │                                            │
│ ├─ release (3) │ 🤖 FreakingJSON-PA                         │
│ ├─ skills (5)  │ │ Mostrando sesión: Release v0.1.2...     ││
│ └─ ...         │                                            │
└────────────────┴────────────────────────────────────────────┘
```

---

## 6. BACKLOG TRACEABILITY

| Backlog ID | Requirement | Status |
|------------|-------------|--------|
| FE-001 | Dashboard SPA | In Progress |
| UX-001 | Onboarding Process | In Progress |
| UX-004 | Chat UI | In Progress (modo lectura) |
| UX-007 | About Us | In Progress |
| INF-003 | Knowledge Base | Done |
| BL-086 | Interactions Log | Done |
| FE-004 | Chat UI Integración Completa | Backlog (futuro) |

---

## 7. DELIVERY

### Milestones

#### M1: Core Structure (Día 1)
- [ ] HTML base con Tailwind inline
- [ ] Router SPA vanilla JS
- [ ] Componentes base (Header, Sidebar, Content)

#### M2: Data Integration (Día 1-2)
- [ ] Cargar sessions-index.json
- [ ] Renderizar lista de sesiones
- [ ] Mostrar contenido de sesión

#### M3: UI Polish (Día 2)
- [ ] Estilos ChatGPT-like
- [ ] Responsive design
- [ ] Animaciones y transiciones

#### M4: Search & Extras (Día 2-3)
- [ ] Integrar búsqueda
- [ ] Framework Internals
- [ ] About Us con redes

### Dependencies
- sessions-index.json (existente)
- search-index.db (existente)
- skills catalog (existente)

### Risks
| Risk | Mitigation |
|------|------------|
| Tamaño >1MB | Optimizar assets, lazy loading |
| Performance en muchas sesiones | Virtual scrolling |
| Compatibilidad navegadores | Testing en múltiples browsers |

### Rollout Plan
1. Generar dashboard.html
2. Testing local
3. Commit a repo
4. Actualizar pa.bat/sh para abrir dashboard
5. Documentar en README

---

## 8. APPENDIX

### Resources
- Design System: A generar con @ui-ux-pro-max
- Inspiration: ChatGPT, DeepSeek, Claude
- Icons: Heroicons
- Charts: Chart.js

### Open Questions
- ¿Incluir modo oscuro/claro?
- ¿Exportar sesiones como PDF?
- ¿Integrar con notificaciones del sistema?

---

*PRD generado siguiendo estándares @prd-generator*
*Framework: FreakingJSON Personal Assistant*

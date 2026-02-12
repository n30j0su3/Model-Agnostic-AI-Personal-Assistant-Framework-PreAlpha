# Roadmap

Plan de desarrollo del Personal Assistant Framework.

---

## Versiones Alpha

### ✅ v0.1.0-alpha (Actual)
**Fecha**: 2026-02-11

Primera release con arquitectura base estable:
- 4 skills nuevas (skill-creator, markdown-writer, csv-processor, python-standards)
- 5 agentes desplegados
- Sistema de sync BASE/DEV/PROD
- 28 scripts validados cross-platform

---

## v0.2.0-alpha (En Planificación)
**Objetivo**: Interfaz visual básica para configuración

### Features Planificadas

#### 1. Dashboard Web Básico
- [ ] **Visualizador de Skills**: Grid con todas las skills disponibles
  - Iconos por categoría
  - Estado (enabled/disabled)
  - Metadata (versión, autor, descripción)
  - Botón de activar/desactivar

- [ ] **Configurador de Agente**: 
  - Dropdown para seleccionar agente principal
  - Checkboxes para subagentes activos
  - Preview de configuración en tiempo real

- [ ] **Gestor de Workspaces**:
  - Lista de workspaces existentes
  - Crear nuevo workspace (formulario)
  - Switch entre workspaces

#### 2. Mejoras de Framework
- [ ] Sistema de plugins para skills
- [ ] Tests automatizados para todas las skills
- [ ] Documentación interactiva

---

## v0.3.0-alpha (Futuro)
**Objetivo**: Chat integrado y funcionalidades avanzadas

### Features Planificadas

#### 1. Chat Interface
- [ ] **Ventana de chat** integrada con @pa-assistant
- [ ] **Historial de conversaciones** por sesión
- [ ] **Comandos slash** (/status, /session, /skill, etc.)
- [ ] **Sugerencias contextuales** basadas en workspace activo

#### 2. Visualización de Contexto
- [ ] **Explorador de archivos** .md del contexto
- [ ] **Buscador** con filtros por tipo (skills, agents, sessions)
- [ ] **Editor visual** para archivos de configuración

#### 3. Automatización
- [ ] **Scheduler** para tareas recurrentes
- [ ] **Workflows** visuales (drag & drop)
- [ ] **Integraciones** con servicios externos (APIs)

---

## v1.0.0 (Release Estable)
**Objetivo**: Versión 1.0 estable sin alpha

### Criterios de Salida de Alpha
- [ ] Dashboard SPA completo y estable
- [ ] +20 skills en el catálogo
- [ ] Documentación completa (técnica + usuario)
- [ ] Tests de integración >80% cobertura
- [ ] Comunidad activa de contribuidores

### Features v1.0
- [ ] **Marketplace de Skills**: Repositorio público de skills de la comunidad
- [ ] **Multi-usuario**: Soporte para perfiles múltiples
- [ ] **Sync en la nube**: Opcional, cifrado end-to-end
- [ ] **Mobile app**: Acompañante móvil básico

---

# 💡 Ideas para Dashboard SPA

> Notas para cuando planifiquemos el desarrollo del Dashboard

## Concepto General
SPA (Single Page Application) que sirva como interfaz visual del framework, integrada con opencode y accesible desde navegador.

## Stack Tecnológico Sugerido

### Opción A: React + TypeScript (Recomendada)
- **Pros**: Mayor ecosistema, más librerías, más desarrolladores
- **Cons**: Boilerplate inicial más pesado
- **Librerías UI**: shadcn/ui, Tailwind, Radix
- **Estado**: Zustand o Redux Toolkit
- **Comunicación**: WebSocket con backend opencode

### Opción B: Vue 3 + TypeScript
- **Pros**: Más simple, mejor DX, reactividad nativa
- **Cons**: Menos librerías especializadas
- **Librerías UI**: Nuxt UI, Element Plus
- **Estado**: Pinia
- **Comunicación**: WebSocket o Server-Sent Events

### Opción C: Svelte + SvelteKit
- **Pros**: Performance, menos código, compilación
- **Cons**: Curva de aprendizaje diferente, menos maduro
- **Librerías UI**: Skeleton, shadcn-svelte

## Features del Dashboard (Brainstorming)

### Core
1. **Visualizador de Skills**
   - Grid con tarjetas de skills
   - Iconos dinámicos según categoría
   - Toggle on/off
   - Configuración por skill

2. **Chat Interface**
   - Ventana de chat tipo Slack/Discord
   - Historial persistente
   - Soporte markdown en mensajes
   - Archivos adjuntos

3. **Settings Panel**
   - Preferencias de usuario
   - Configuración de CLI por defecto
   - Integraciones (API keys, tokens)
   - Tema (light/dark)

4. **Workspace Manager**
   - Vista tipo Finder/Explorer
   - Drag & drop de archivos
   - Preview de archivos .md
   - Búsqueda global

### Avanzadas
5. **Live Status**: Estado de sincronización entre entornos BASE/DEV/PROD
6. **Session Timeline**: Visualización de sesiones pasadas
7. **Skill Builder**: Wizard visual para crear nuevas skills
8. **Analytics**: Uso de skills, sesiones, comandos más usados

### Integraciones
- **GitHub**: Crear issues, ver PRs
- **Notion/Obsidian**: Sync de notas
- **Calendar**: Integración con Google Calendar/Outlook
- **Email**: Lectura/respuesta rápida

## Arquitectura Propuesta

```
┌─────────────────────────────────────────┐
│           Dashboard SPA                 │
│  (React/Vue/Svelte + WebSocket)         │
└─────────────────┬───────────────────────┘
                  │ WebSocket
┌─────────────────▼───────────────────────┐
│         Opencode Bridge                 │
│  (MCP Server o HTTP API)                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      PA Framework Core                  │
│  (scripts/skills/agents)                │
└─────────────────────────────────────────┘
```

## Prioridades MVP (Minimum Viable Product)

Para v0.2.0-alpha, enfocarse en:
1. Visualizador de skills con toggle on/off
2. Selector de agente principal
3. Vista básica de workspaces
4. Conexión WebSocket básica

## Notas de Implementación

- Mantener filosofía local-first: dashboard corre localmente
- Sin dependencias de servicios cloud para funcionar básico
- Opcional: sync con cloud cifrado para backups
- Responsive: debe funcionar en tablet para movilidad

---

*Última actualización: 2026-02-11*
*Estado del roadmap: En desarrollo activo*

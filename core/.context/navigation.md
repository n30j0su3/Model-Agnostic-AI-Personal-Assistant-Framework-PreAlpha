# Context Navigation

**Purpose**: Mapa central del conocimiento del framework. Punto de entrada para agentes AI.

---

## Structure

```
core/.context/
├── MASTER.md              # Fuente de verdad (configuración global)
├── navigation.md          # Este archivo — mapa de navegación
├── sessions/              # Sesiones diarias (YYYY-MM-DD.md)
├── codebase/              # Conocimiento persistente del usuario
│   ├── recordatorios.md   # Tareas y recordatorios
│   └── ideas.md           # Ideas, enlaces, notas
└── backups/               # Backups automáticos de contexto
```

---

## Quick Routes

| Tarea | Ruta |
|-------|------|
| **Ver configuración global** | `MASTER.md` |
| **Sesión de hoy** | `sessions/YYYY-MM-DD.md` |
| **Recordatorios** | `codebase/recordatorios.md` |
| **Ideas y notas** | `codebase/ideas.md` |
| **Agentes disponibles** | `../agents/AGENTS.md` |
| **Skills disponibles** | `../skills/SKILLS.md` |

---

## By Category

**MASTER.md** — Configuración global, idioma, workspaces, preferencias
**sessions/** — Historial diario, logs de sesiones AI, trazabilidad
**codebase/** — Base de conocimiento personal (persistente entre sesiones)
**../agents/** — Definiciones de agentes y subagentes
**../skills/** — Habilidades modulares invocables

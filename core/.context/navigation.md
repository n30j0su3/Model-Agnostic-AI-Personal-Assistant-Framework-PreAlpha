# Navigation — PA Framework

> Archivo de navegación rápida para el framework.
> Creado automáticamente — referencia central de archivos clave.

---

## 🔗 Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `core/.context/MASTER.md` | Contexto maestro del framework |
| `core/.context/quick-start.md` | Inicio rápido (<500 tokens para agentes) |
| `core/.context/profile.md` | Perfil de instalación del usuario |
| `core/.context/sessions/` | Sesiones diarias (YYYY-MM-DD.md) |
| `core/.context/codebase/` | Notas, ideas, recordatorios |
| `core/.context/knowledge/` | Knowledge Base indexada |
| `core/agents/pa-assistant.md` | Agente principal orquestador |
| `core/agents/subagents/` | Subagentes especializados |
| `core/skills/SKILLS.md` | Catálogo completo de skills |
| `workspaces/` | Directorios de trabajo |
| `config/branding.txt` | Banner de presentación |
| `VERSION` | Versión actual del framework |

---

## 📋 Referencia Rápida

### Comandos principales
```bash
# Iniciar framework
./pa.sh           # Linux/Mac
pa.bat            # Windows

# Scripts principales
python core/scripts/pa.py           # Menú interactivo
python core/scripts/install.py      # Instalación inicial
python core/scripts/session_start.py  # Iniciar sesión
python core/scripts/session_end.py    # Cerrar sesión
python core/scripts/update.py        # Actualizar framework
python core/scripts/memory_pipeline.py  # Pipeline de memoria
```

### Rutas de documentación
- `README.md` → Guía de inicio
- `docs/` → Documentación técnica
- `CHANGELOG.md` → Historial de cambios
- `AGENTS.md` → Documentación de agentes

---

*Última actualización: 2026-04-28 | Framework v0.3.8-alpha*

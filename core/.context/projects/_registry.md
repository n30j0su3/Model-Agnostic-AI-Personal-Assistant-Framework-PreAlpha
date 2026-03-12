# Projects Registry

> Registro central de proyectos gestionados por el framework PA.

## Uso

Este directorio almacena contexto específico de proyectos. Cada proyecto puede tener su propia estructura:

```
projects/
├── _registry.md          # Este archivo - índice de proyectos
└── {project-name}/       # Directorio del proyecto
    ├── .context/         # Contexto local del proyecto
    │   ├── config.md     # Configuración específica
    │   └── notes.md      # Notas y decisiones
    └── README.md         # Descripción del proyecto
```

## Proyectos Registrados

| Proyecto | Workspace | Ubicación | Estado |
|----------|-----------|-----------|--------|
| *(ninguno registrado)* | - | - | - |

## Registro de Nuevo Proyecto

Para registrar un proyecto, crear entrada en la tabla superior y opcionalmente un directorio con contexto.

---

> **Nota**: Los proyectos también pueden residir en `workspaces/{workspace}/projects/` para aislamiento completo.
> 
> **Creado**: 2026-03-11 — Sistema de migración v0.2.0
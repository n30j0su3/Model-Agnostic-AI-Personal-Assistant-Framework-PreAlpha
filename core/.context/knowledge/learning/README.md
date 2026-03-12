# Learning Hub

> Sistema de aprendizaje continuo del framework. Extrae, almacena y recupera conocimiento valioso de las sesiones.

## Estructura

```
learning/
├── README.md           # Este archivo
├── discoveries.md      # Hallazgos significativos
├── anti-patterns.md    # Patrones negativos detectados
└── best-practices.md   # Mejores prácticas emergentes
```

## Uso

### Registrar un hallazgo
```markdown
## 2026-03-11: Flujo de sesión cerrado

**Hallazgo**: El flujo de inicio/cierre de sesión es crítico para la persistencia del conocimiento.
**Impacto**: Sin session-end.py, las sesiones quedan en estado "active" indefinidamente.
**Acción**: Siempre ejecutar session-end.py al terminar.
```

### Tipos de contenido

| Archivo | Contenido | Ejemplo |
|---------|-----------|---------|
| `discoveries.md` | Ideas nuevas, soluciones innovadoras | "Usar importlib para scripts con guiones" |
| `anti-patterns.md` | Lo que NO funciona, errores comunes | "No confiar en memoria de conversación" |
| `best-practices.md` | Patrones probados que funcionan | "SIEMPRE leer archivo antes de editarlo" |

## Integración

- **Extracción automática**: `knowledge-indexer.py` puede extraer patrones
- **Referencia desde sesión**: Los agentes pueden consultar este hub
- **Actualización**: Al cerrar sesión con session-end.py

---

> *"El aprendizaje continuo es la base de la mejora sistemática."*
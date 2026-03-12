# Prompts Registry

> Colección de prompts exitosos reutilizables. El framework aprende qué prompts funcionan mejor.

## Estructura

```
prompts/
├── README.md           # Este archivo
└── registry.json       # Registro de prompts exitosos
```

## Categorías

| Categoría | Descripción |
|-----------|-------------|
| `analysis` | Análisis de código/datos |
| `generation` | Generación de contenido |
| `debugging` | Debug y troubleshooting |
| `documentation` | Crear documentación |
| `planning` | Planificación y arquitectura |

## Uso

### Registrar un prompt exitoso

En `registry.json`:
```json
{
  "id": "analyze-structure",
  "category": "analysis",
  "prompt": "Analiza la estructura de {target} y...",
  "context": "Útil para entender proyectos desconocidos",
  "success_rate": 0.95,
  "last_used": "2026-03-11"
}
```

### Reutilizar un prompt

1. Buscar en registry por categoría
2. Copiar template
3. Reemplazar placeholders
4. Ejecutar

## Integración

- **Detección automática**: Pendiente implementar
- **Rating manual**: Usuario puede marcar prompt como exitoso
- **Extracción**: Desde interactions/*.jsonl

---

> *"Un buen prompt es la mitad del trabajo hecho."*
# Self-Healing Hub

> Sistema de recuperación automática de errores. El framework aprende de sus errores y se auto-repara.

## Estructura

```
self-healing/
├── README.md           # Este archivo
├── error-log.jsonl     # Log de errores encontrados
└── playbooks/          # Recovery playbooks
    ├── README.md
    ├── encoding-error.md
    ├── file-not-found.md
    └── permission-denied.md
```

## Filosofía

> **"El error como combustible"** - CORE-003

Cada error es una oportunidad de mejora:
1. **Documentar** → No perder el conocimiento
2. **Analizar** → Entender causa raíz
3. **Recuperar** → Aplicar solución
4. **Aprender** → Prevenir recurrencia

## Uso

### Registrar un error

```json
{"timestamp":"2026-03-11T10:30:00","session":"2026-03-11","error_type":"FileNotFoundError","message":"sessions/2026-03-11.md not found","context":{"file":"sessions/2026-03-11.md","operation":"read"},"resolved":true,"resolution":"Created session file via session-start.py"}
```

### Crear un playbook

1. Identificar error recurrente (aparece 3+ veces)
2. Crear archivo en `playbooks/{error-type}.md`
3. Documentar: síntomas, causa, solución, prevención

## Integración

| Fase | Acción |
|------|--------|
| **Detección** | session-end.py detecta errores |
| **Logging** | @error-recovery loguea en error-log.jsonl |
| **Análisis** | pattern-analyzer detecta recurrencia |
| **Playbook** | Si recurrente, generar playbook |

---

> *"Un sistema que aprende de sus errores es más fuerte que uno que nunca falla."*
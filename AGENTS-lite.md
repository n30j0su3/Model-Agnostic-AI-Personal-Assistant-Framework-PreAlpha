# AGENTS-lite — Bootstrap Minimal (Tier 0)

> **Version: v0.3.8-alpha**

## ✅ Inicialización rápida

```bash
python core/scripts/session_start.py
```

Si el script no está disponible, cargar en este orden:

1. `AGENTS.md` (router operativo)
2. `core/.context/MASTER.md` (config global)
3. `core/skills/SKILLS.md` (skills obligatorias)

## 🧠 Memoria persistente (regla simple)

- `.md` sessions = universal (siempre)
- `SQLite` = consultas estructuradas
- `Memory MD` = conocimiento reutilizable
- `Wiki` = documentación formal

Referencia completa: `docs/MEMORY-ARCHITECTURE.md`

## 🔚 Cierre

```bash
python core/scripts/session_end.py
```

> Documento completo: `AGENTS-full.md`

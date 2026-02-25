# Reporte de Validacion DEV - Pre-Sync

**Fecha:** 2026-02-24T23:04:09.581471
**DEV Path:** `C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV`
**BASE Path:** `N/A`

---

## Resumen Ejecutivo

- **Recursos criticos totales:** 10
- **Recursos presentes:** [OK] 4
- **Recursos faltantes:** [MISSING] 6
- **Nuevos en BASE:** [NEW] 0
- **Conflictos potenciales:** [CONFLICT] 0
- **Score de integridad:** 40.0%

---

## Recursos Presentes

| Recurso | Tipo | Tamaño | MD5 |
|---------|------|--------|-----|
| `core/.context/workspaces/maaji.md` | [FILE] | 5,437 bytes | 415dbfa8... |
| `workspaces/development` | [DIR] | - | - |
| `workspaces/personal` | [DIR] | - | - |
| `workspaces/professional/projects/Maaji` | [DIR] | - | - |

---

## Recursos Faltantes

Los siguientes recursos criticos NO fueron encontrados:

- [MISSING] `core/agents/subagents/_local/maaji/maaji-master.md`
- [MISSING] `core/skills/_local/maaji/atribucion/SKILL.md`
- [MISSING] `core/skills/_local/maaji/checkout-con-evento/SKILL.md`
- [MISSING] `core/skills/_local/maaji/checkout-sin-evento/SKILL.md`
- [MISSING] `core/skills/_local/maaji/klaviyo-extract/SKILL.md`
- [MISSING] `docs/MAAJI-PROMOTION-GUIDE.md`

---

## Recomendaciones para Sync Seguro

1. [WARNING] **ATENCION CRITICA:** Existen recursos faltantes. Verificar antes de sync.
3. [OK] Realizar backup de DEV antes del sync
4. [OK] Verificar que los agentes locales de Maaji no se sobrescriban
5. [OK] Confirmar que las 4 skills de Maaji permanezcan intactas
6. [OK] Validar workspaces de professional/personal/development post-sync

---

*Reporte generado automaticamente por validate-dev-resources.py*
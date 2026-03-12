---
description: Muestra estado actual del framework (KPIs, métricas, sesión activa)
agent: FreakingJSON
---

# Estado del Framework FreakingJSON-PA

## 1. Sesión Activa
- Lee core/.context/sessions/YYYY-MM-DD.md (fecha actual)
- Muestra: hora inicio, temas tratados, decisiones, pendientes

## 2. Métricas de Uso (últimos 30 días)
- Sesiones totales
- Horas de interacción (estimado: sesiones × duración promedio)
- Horas ahorradas (framework vs tradicional)

## 3. Proyectos Activos
- Lee workspaces/ de MASTER.md
- Cuenta proyectos por workspace

## 4. Framework Stats
- Skills disponibles (core/skills/catalog.json)
- Agentes activos (core/agents/AGENTS.md)
- Optimizaciones aplicadas (si existe log)

## 5. Pendientes
- Lee core/.context/codebase/recordatorios.md
- Muestra: total pendientes, completados hoy

## 6. Tendencias (opcional, si hay datos históricos)
- Frases/patrones más empleados
- Área/categoría más usada
- Modelo/CLI más empleado

**Formato**: KPIs concisos, bullets, tabla si aplica.

**Nota**: Este comando es específico del framework FreakingJSON-PA, NO es el `/status` de OpenCode CLI.

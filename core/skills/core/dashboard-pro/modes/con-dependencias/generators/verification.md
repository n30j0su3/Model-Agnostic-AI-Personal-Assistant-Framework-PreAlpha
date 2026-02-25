# Prompt: Verification
# Skill: dashboard-pro

## Context
Verifica la calidad del dashboard generado antes de entregar.

## Design Specification
{{design_spec_jsonc}}

## Generated Code
{{generated_code}}

## Verification Checklist

### 1. Estructura de Código
- [ ] ¿Los componentes están separados en archivos individuales?
- [ ] ¿Los datos mock están en archivo separado?
- [ ] ¿Los tipos TypeScript están definidos?
- [ ] ¿No hay archivos monolíticos (>300 líneas)?
- [ ] ¿Las importaciones son limpias y ordenadas?

### 2. Diseño Visual
- [ ] ¿Los colores coinciden con el design spec?
- [ ] ¿La tipografía es consistente?
- [ ] ¿El espaciado sigue la escala definida?
- [ ] ¿Los bordes y radios son consistentes?
- [ ] ¿No hay valores hardcodeados (hex, px)?

### 3. Responsive
- [ ] ¿Funciona en mobile (375px)?
- [ ] ¿Funciona en tablet (768px)?
- [ ] ¿Funciona en desktop (1440px)?
- [ ] ¿Los layouts se adaptan correctamente?
- [ ] ¿El texto no se desborda?
- [ ] ¿Los gráficos son legibles en mobile?

### 4. Dark/Light Mode
- [ ] ¿El toggle funciona?
- [ ] ¿Todos los elementos cambian de color?
- [ ] ¿Los gráficos adaptan colores?
- [ ] ¿No hay elementos "hardcodeados" a un modo?
- [ ] ¿El contraste es adecuado en ambos modos?

### 5. Funcionalidad
- [ ] ¿Los KPIs muestran datos correctos?
- [ ] ¿Los gráficos renderizan con datos mock?
- [ ] ¿Las tablas tienen sorting?
- [ ] ¿Las tablas tienen pagination?
- [ ] ¿Los tooltips funcionan?
- [ ] ¿Las navegaciones son clickeables?

### 6. Accesibilidad
- [ ] ¿Hay atributos ARIA donde aplique?
- [ ] ¿Los colores tienen suficiente contraste?
- [ ] ¿Los botones tienen nombres descriptivos?
- [ ] ¿Los inputs tienen labels asociados?
- [ ] ¿El foco es visible?

### 7. Performance
- [ ] ¿No hay renders innecesarios?
- [ ] ¿Los charts usan ResponsiveContainer?
- [ ] ¿Las animaciones son suaves (60fps)?
- [ ] ¿No hay memory leaks?

### 8. TypeScript
- [ ] ¿No hay errores de tipo?
- [ ] ¿Las props están tipadas?
- [ ] ¿Los generics se usan correctamente?
- [ ] ¿No hay `any` innecesarios?

## Output

Generar reporte de verificación:

```markdown
# Verification Report

## Score: X/8 categorías aprobadas

## Issues Encontradas
{{#if issues}}
{{#each issues}}
- [ ] **{{severity}}**: {{description}}
  - Location: {{file}}:{{line}}
  - Fix: {{suggestion}}
{{/each}}
{{else}}
✅ No issues encontradas
{{/if}}

## Recomendaciones
{{recommendations}}

## Estado
{{#if passed}}
✅ APROBADO para entrega
{{else}}
❌ REQUIERE FIXES antes de entrega
{{/if}}
```

Si hay issues, proporcionar fixes específicos con código.

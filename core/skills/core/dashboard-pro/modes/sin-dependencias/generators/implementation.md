# Prompt: Implementation (HTML Standalone)
# Modo: sin-dependencias
# Skill: dashboard-pro

## Context
Genera un dashboard completo en un solo archivo HTML, sin dependencias externas excepto CDNs.

## Design Brief
{{design_brief}}

## Design Specification
{{design_spec_jsonc}}

## Template Base

```html
<!DOCTYPE html>
<html lang="es" class="{{default_theme}}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{project_title}}</title>
  
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- Chart Library CDN -->
  {{#if chart_library == 'chart-js'}}
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  {{/if}}
  {{#if chart_library == 'apex-charts'}}
  <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
  {{/if}}
  
  <!-- Configuración Tailwind -->
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            primary: {
              DEFAULT: '{{colors.primary.main}}',
              light: '{{colors.primary.light}}',
              dark: '{{colors.primary.dark}}',
            },
            // ... más colores
          }
        }
      }
    }
  </script>
  
  <!-- Estilos CSS -->
  <style>
    /* Variables CSS para theming */
    :root {
      --background: {{colors.light.background}};
      --foreground: {{colors.light.foreground}};
      /* ... */
    }
    
    .dark {
      --background: {{colors.dark.background}};
      --foreground: {{colors.dark.foreground}};
      /* ... */
    }
    
    /* Utilidades personalizadas */
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)]">
  <!-- Contenido -->
  
  <script>
    // JavaScript vanilla
    // Datos mock
    // Inicialización de charts
    // Toggle dark mode
  </script>
</body>
</html>
```

## Requirements Checklist

### Estructura HTML
- [ ] Documento HTML5 válido
- [ ] Meta viewport para responsive
- [ ] CDN de Tailwind CSS
- [ ] CDN de librería de charts (si aplica)
- [ ] Configuración Tailwind inline
- [ ] CSS variables para theming
- [ ] JavaScript vanilla embebido

### UI/UX
- [ ] **Mobile-first**: Diseñar para mobile primero
- [ ] **Dark/Light mode**: Toggle funcional con clase `dark`
- [ ] **No valores hardcodeados**: Usar CSS variables o clases Tailwind
- [ ] **SVG inline**: Iconos como SVG, no imágenes externas
- [ ] **Tipografía consistente**: Tailwind font classes

### Componentes
- [ ] **KPI Cards**: Tarjetas con métricas clave
- [ ] **Charts**: Gráficos funcionales con Chart.js/ApexCharts/vanilla
- [ ] **Tables**: Tablas HTML nativas estilizadas
- [ ] **Navigation**: Sidebar o top nav responsive
- [ ] **Header**: Con toggle de tema y título

### JavaScript
- [ ] **Datos embebidos**: Array de objetos JS en el script
- [ ] **Charts inicializados**: new Chart() o ApexCharts()
- [ ] **Dark mode toggle**: Cambia clase en <html>
- [ ] **Responsive**: Event listeners para resize
- [ ] **Sin frameworks**: Solo vanilla JS

### Charts según librería

#### Chart.js
```javascript
const ctx = document.getElementById('myChart').getContext('2d');
new Chart(ctx, {
  type: 'line',
  data: { labels: [], datasets: [] },
  options: { responsive: true, maintainAspectRatio: false }
});
```

#### ApexCharts
```javascript
const options = {
  chart: { type: 'line', height: 350 },
  series: [{ data: [] }]
};
new ApexCharts(document.querySelector("#chart"), options).render();
```

#### Vanilla SVG
```javascript
// Generar SVG paths dinámicamente
// Usar viewBox para escalado
```

### Optimización
- [ ] Código minificado (opcional)
- [ ] Sin comentarios innecesarios
- [ ] Datos mock realistas pero compactos
- [ ] Uso eficiente de Tailwind (evitar clases redundantes)

## Implementation Steps

1. **HTML skeleton**: Estructura base con CDNs
2. **Tailwind config**: Colores y tema según design spec
3. **CSS variables**: Para theming dinámico
4. **Layout**: Sidebar + main content
5. **Components**: KPI cards, charts containers, tables
6. **JavaScript**:
   - Datos mock
   - Inicialización charts
   - Toggle dark mode
   - Responsive handlers
7. **Testing**: Abrir en navegador, verificar responsive y dark mode

## Verification

- [ ] Abre correctamente en Chrome/Firefox/Safari
- [ ] Responsive funciona (redimensionar ventana)
- [ ] Dark mode toggle funciona
- [ ] Charts renderizan con datos
- [ ] No hay errores en consola (F12)
- [ ] Sin dependencias rotas (verificar CDNs cargan)

## Output

Un solo archivo HTML completo y funcional.

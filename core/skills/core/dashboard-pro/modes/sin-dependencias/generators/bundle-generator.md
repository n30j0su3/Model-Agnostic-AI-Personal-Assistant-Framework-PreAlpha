# Prompt: Bundle Generator
# Modo: sin-dependencias
# Skill: dashboard-pro

## Context
Combina todos los componentes en un solo archivo HTML optimizado.

## Components
{{components_code}}

## Styles
{{css_code}}

## Scripts
{{javascript_code}}

## Data
{{mock_data}}

## Task
Generar un archivo HTML único que combine todo lo anterior en un documento válido y funcional.

## Bundle Requirements

1. **Single File**: Todo en un archivo .html
2. **No External Assets**: Todo inline (excepto CDNs)
3. **Optimized**: Eliminar espacios innecesarios (opcional)
4. **Valid HTML5**: Pasar validador W3C
5. **Self-Contained**: Funciona offline después de cargar CDNs

## Output Structure

```html
<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{project_name}}</title>
  
  <!-- CDNs -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- CDN Chart Library -->
  
  <!-- Tailwind Config -->
  <script>...tailwind.config...</script>
  
  <!-- CSS Styles -->
  <style>...custom css...</style>
</head>
<body>
  <!-- HTML Structure -->
  
  <!-- JavaScript -->
  <script>
    // Datos
    // Funciones
    // Inicialización
  </script>
</body>
</html>
```

## Optimizations

- Minimizar HTML (eliminar espacios entre tags)
- Consolidar CSS
- Optimizar JavaScript
- Lazy load charts si hay muchos

## File Size Target

- Simple dashboard: < 200KB
- Medium complexity: < 500KB
- Complex dashboard: < 1MB

## Output

Archivo HTML único listo para usar.

# @dashboard-pro — Dashboard Pro Generator

> Genera dashboards profesionales con diseño consistente y código mantenible.
> 
> *"El conocimiento verdadero trasciende a lo público."*

---

## 🚀 Uso Rápido

```bash
# Modo con dependencias (Next.js completo)
@dashboard-pro mode=con-dependencias "Dashboard de analytics para SaaS de email marketing"

# Modo sin dependencias (HTML único)
@dashboard-pro mode=sin-dependencias chart-library=chart-js "Reporte de ventas Q4"

# Con preset de estilo
@dashboard-pro style-preset=fintech-dark "Exchange de criptomonedas"
```

---

## 📋 Modos de Operación

### 1. `con-dependencias` — Proyecto Next.js Completo

**Ideal para**: Proyectos grandes, aplicaciones de producción, código mantenible.

**Stack**:
- Next.js 15 (App Router)
- React 19 + TypeScript
- Tailwind CSS 3.4
- shadcn/ui (50+ componentes)
- Recharts (gráficos)
- TanStack Table (tablas avanzadas)
- Framer Motion (animaciones)

**Entregable**:
```
📦 mi-dashboard/
├── app/
├── components/
├── lib/
├── types/
├── package.json
└── ...
```

**Comandos**:
```bash
cd mi-dashboard
npm install
npm run dev     # localhost:3000
npm run build   # Optimizado para producción
```

---

### 2. `sin-dependencias` — Archivo HTML Único

**Ideal para**: Entregables rápidos, reportes, prototipos, compartir vía email.

**Características**:
- Un solo archivo `.html`
- Tailwind CSS via CDN
- Charts via CDN (sin build)
- Responsive mobile-first
- Listo para abrir directamente

**Entregable**:
```
📄 dashboard-ventas-q4.html   # ~200-500KB
```

**Uso**:
```bash
# Simplemente abre en navegador
open dashboard-ventas-q4.html

# O sirve con cualquier servidor estático
npx serve .
```

---

## 🎨 Librerías de Charts (modo sin-dependencias)

| Prioridad | Librería | Cuándo usar | Tamaño |
|-----------|----------|-------------|--------|
| **1** | Chart.js | Default. Balance funcionalidad/peso | ~60KB |
| **2** | ApexCharts | Gráficos avanzados (heatmap, radar) | ~80KB |
| **3** | Vanilla SVG | Ultra-ligero, simple, cero deps | ~0KB |

**Selección automática**:
```
Complejidad alta → Chart.js
Complejidad media → Chart.js
Complejidad baja/simple → Vanilla SVG
Requerimientos específicos → ApexCharts (explícito)
```

---

## 🎯 Presets de Estilo

| Preset | Descripción | Uso típico |
|--------|-------------|------------|
| `fintech-dark` | Dark + Gold premium | Exchanges, trading, wallets |
| `fintech-light` | Light + Blue | Banking, corporate apps |
| `saas-modern` | Light + Purple gradient | Startups, SaaS moderno |
| `enterprise` | Neutro corporativo | Admin panels, B2B |
| `custom` | Definido en Design Brief | Cualquier diseño específico |

---

## 📖 Workflow Completo

### Paso 1: Descripción
Usuario describe el dashboard que necesita:
```
"Necesito un dashboard de analytics para una plataforma de email marketing.
Debe mostrar: métricas de envío, tasas de apertura/clics, gráfico de 
crecimiento de suscriptores, tabla de últimas campañas. Estilo SaaS moderno."
```

### Paso 2: Generación Design Brief
La skill genera un Design Brief en JSONC con:
- Metadatos del proyecto
- Theme (colores, tipografía)
- Layout (grid, breakpoints)
- Componentes (KPIs, charts, tablas)
- Datos mock

### Paso 3: Aprobación
Usuario revisa y aprueba el brief (o solicita cambios).

### Paso 4: Implementación
La skill genera el código según el modo seleccionado.

### Paso 5: Verificación
Checks automáticos de calidad (responsive, dark mode, etc.)

### Paso 6: Entrega
Proyecto completo o archivo HTML listo para usar.

---

## 🛠️ Integración con Agentes

### Uso Directo
```
Usuario: @dashboard-pro "Dashboard de ventas"
```

### Desde @feature-architect
```
Usuario: Quiero agregar un dashboard al proyecto
dashboard-pro: Detectado requerimiento de dashboard
               → Delegando a @dashboard-pro
```

---

## 📁 Estructura de la Skill

```
core/skills/dashboard-pro/
├── skill.yaml              # Configuración y metadata
├── README.md               # Este archivo
├── CONFIG.md               # Guía de configuración
│
├── modes/
│   ├── con-dependencias/
│   │   ├── templates/
│   │   │   └── nextjs-dashboard/     # Template Next.js
│   │   └── generators/
│   │       ├── design-brief.md       # Prompt brief
│   │       ├── implementation.md     # Prompt implementación
│   │       └── verification.md       # Prompt verificación
│   │
│   └── sin-dependencias/
│       ├── templates/
│       │   ├── chart-js/             # Template Chart.js
│       │   ├── apex-charts/          # Template ApexCharts
│       │   └── vanilla-svg/          # Template Vanilla
│       └── generators/
│           ├── design-brief.md
│           ├── implementation.md
│           └── bundle-generator.md   # Combina en HTML
│
├── schemas/
│   ├── design-tokens.json            # Schema JSONC
│   └── component-library.json        # Componentes disponibles
│
├── examples/
│   ├── design-brief-fintech.jsonc    # Ejemplo brief
│   ├── con-dependencias-example/     # Ejemplo Next.js
│   └── sin-dependencias-example/     # Ejemplo HTML
│
└── utils/
    ├── template-renderer.js
    ├── dependency-mapper.js
    └── bundler.js
```

---

## 🔧 Personalización

### Colores Personalizados
Edita `CONFIG.md` o proporciona en el Design Brief:
```jsonc
{
  "colors": {
    "primary": "#6366F1",
    "secondary": "#8B5CF6",
    "background": "#0F172A"
  }
}
```

### Componentes Adicionales
Extiende el schema en `schemas/component-library.json`:
```json
{
  "components": {
    "custom": ["Heatmap", "Sankey", "Gantt"]
  }
}
```

### Templates Propios
Coloca templates en `modes/{mode}/templates/custom-{nombre}/`

---

## 📝 Ejemplos

### Ejemplo 1: Dashboard Fintech (Con Dependencias)
```bash
@dashboard-pro 
  mode=con-dependencias 
  style-preset=fintech-dark 
  "Exchange de criptomonedas con balance, historial de trades, 
   gráfico de precios, y tabla de órdenes abiertas"
```

### Ejemplo 2: Reporte de Ventas (Sin Dependencias)
```bash
@dashboard-pro 
  mode=sin-dependencias 
  chart-library=chart-js 
  "Reporte mensual de ventas con KPIs, gráfico de tendencias, 
   y tabla de top productos"
```

### Ejemplo 3: Analytics SaaS (Vanilla)
```bash
@dashboard-pro 
  mode=sin-dependencias 
  chart-library=vanilla-svg 
  "Dashboard simple de métricas: usuarios activos, 
   revenue, churn rate. Ultra-ligero para email."
```

---

## ✅ Checklist de Calidad

Todo dashboard generado incluye:

- [ ] Responsive (mobile → desktop)
- [ ] Dark/light mode (donde aplique)
- [ ] Datos mock realistas
- [ ] Tooltips en gráficos
- [ ] Estados de carga (skeletons)
- [ ] Estados vacíos
- [ ] Accesibilidad básica (ARIA)
- [ ] TypeScript estricto (modo con-deps)
- [ ] Código modular y mantenible

---

## 🆘 Troubleshooting

### Modo con-dependencias

**Error: `Module not found`**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Error: `Tailwind classes not working`**
Verifica que `tailwind.config.ts` incluya las rutas correctas:
```js
content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}']
```

### Modo sin-dependencias

**Charts no renderizan**
- Verifica conexión a internet (CDN requerido)
- Abre consola del navegador (F12) para errores

**Tailwind no aplica estilos**
- El CDN puede tardar en cargar. Recarga la página.
- Verifica que no haya adblockers bloqueando el CDN.

---

## 📚 Recursos Relacionados

- [Vibe Coding Starter Guide](https://pageai.pro/blog/vibe-coding-starter-guide) — Metodología base
- [shadcn/ui](https://ui.shadcn.com) — Componentes UI
- [Recharts](https://recharts.org) — Gráficos React
- [Chart.js](https://www.chartjs.org) — Gráficos vanilla
- [ApexCharts](https://apexcharts.com) — Gráficos avanzados

---

## 🤝 Contribuir

Para extender esta skill:

1. Crea nuevo template en `modes/{mode}/templates/`
2. Agrega preset de estilo en `skill.yaml`
3. Documenta en `CONFIG.md`
4. Agrega ejemplo en `examples/`

---

## 📄 Licencia

MIT — Parte del Framework FreakingJSON.

---

> *"I own my context. I am FreakingJSON."*

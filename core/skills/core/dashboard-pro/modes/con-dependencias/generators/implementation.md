# Prompt: Implementation (Next.js)
# Skill: dashboard-pro

## Context
Implementa un dashboard completo en Next.js 15 basado en el Design Brief proporcionado.

## Design Brief
{{design_brief}}

## Design Specification
{{design_spec_jsonc}}

## Requirements Checklist

### Estructura
- [ ] App Router con layout principal
- [ ] Página `/dashboard` como entry point
- [ ] Componentes modulares (1 componente por archivo)
- [ ] Separación de datos mock en `lib/data.ts`
- [ ] Tipos TypeScript en `types/dashboard.ts`

### UI/UX
- [ ] **Responsive completo**: Mobile-first, breakpoints en sm, md, lg, xl
- [ ] **Dark/Light mode**: Usar ThemeProvider y clases `dark:`
- [ ] **NO magic strings**: Usar tokens Tailwind (bg-primary-500, text-muted-foreground)
- [ ] **NO px valores**: Usar spacing scale (p-4, m-2, gap-6)
- [ ] **NO hex values**: Usar variables CSS o tokens Tailwind

### Componentes UI (shadcn/ui)
Base disponible:
- Card, CardHeader, CardTitle, CardContent, CardFooter
- Button (variants: default, outline, ghost, link)
- Badge, Avatar, AvatarFallback, AvatarImage
- Table, TableHeader, TableBody, TableRow, TableCell, TableHead
- Progress, Separator, Skeleton
- Tabs, TabsList, TabsTrigger, TabsContent
- Tooltip, TooltipProvider, TooltipTrigger, TooltipContent

### Charts (Recharts)
Implementar con:
- LineChart, AreaChart, BarChart, PieChart según especificación
- ResponsiveContainer para adaptabilidad
- CustomTooltip para estilo consistente
- Legend configurable
- Animaciones suaves

### Tablas (TanStack Table)
Implementar con:
- ColumnDef tipado
- Sorting
- Pagination
- Row selection (opcional)

### Tema
```tsx
// ThemeToggle debe estar en el header
import { ThemeToggle } from "@/components/theme-toggle";

// Usar variables CSS definidas en globals.css
// Las variables cambian automáticamente con dark mode
```

### Datos Mock
```typescript
// lib/data.ts
export const mockKpiData = [/* ... */];
export const mockChartData = [/* ... */];
export const mockTableData = [/* ... */];
```

### Animaciones
```tsx
// Usar Framer Motion para animaciones de entrada
import { motion } from "framer-motion";

// Ejemplo:
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
```

## File Structure

```
app/
├── layout.tsx              # Root layout con ThemeProvider
├── globals.css             # Variables CSS, Tailwind
├── page.tsx                # Dashboard principal
├── dashboard/
│   └── page.tsx            # (si es ruta separada)
components/
├── ui/                     # shadcn/ui base (ya existen)
├── dashboard/
│   ├── KpiCard.tsx         # Tarjetas KPI
│   ├── ChartSection.tsx    # Sección de gráficos
│   ├── DataTable.tsx       # Tabla de datos
│   ├── Sidebar.tsx         # Navegación lateral
│   └── Header.tsx          # Header con toggle theme
├── theme-provider.tsx      # Provider de tema
└── theme-toggle.tsx        # Botón toggle
types/
└── dashboard.ts            # Interfaces TypeScript
lib/
├── utils.ts                # cn() y helpers
└── data.ts                 # Datos mock
```

## Code Standards

1. **TypeScript estricto**: Todas las props tipadas
2. **Named exports** para componentes
3. ** barrel exports** en index.ts
4. **JSDoc** para funciones complejas
5. **No console.log** en producción

## Implementation Steps

1. Configurar colores en `tailwind.config.ts` según design spec
2. Actualizar `globals.css` con variables CSS
3. Crear tipos en `types/dashboard.ts`
4. Crear datos mock en `lib/data.ts`
5. Implementar componentes dashboard/
6. Ensamblar página principal
7. Verificar responsive y dark mode

## Verification

Antes de entregar, verificar:
- [ ] `npm run build` completa sin errores
- [ ] Responsive en Chrome DevTools (mobile, tablet, desktop)
- [ ] Toggle dark/light mode funciona
- [ ] Charts renderizan correctamente
- [ ] Tablas son funcionales (sort, pagination)
- [ ] No hay errores en consola

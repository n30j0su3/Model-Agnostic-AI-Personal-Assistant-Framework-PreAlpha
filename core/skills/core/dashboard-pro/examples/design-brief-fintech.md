# CryptoVault Dashboard — Design Brief

## 1. Visión General

**CryptoVault** es un dashboard de exchange de criptomonedas diseñado para traders profesionales. El objetivo es proporcionar una visión completa del portafolio, rendimiento histórico y actividad reciente en una interfaz premium y fácil de usar.

**Usuario objetivo**: Traders de criptomonedas con experiencia, inversores institucionales.

**Métricas clave**:
- Balance total
- Valor del portafolio
- Volumen de trading 24h
- Trades activos

---

## 2. Estilo Visual

**Estilo**: Soft Neumorphism + Premium Fintech
- Fondos oscuros con profundidad
- Acentos dorados/dorados-naranja para highlights
- Sombras suaves y difuminadas
- Bordes mínimos, separación por elevación

**Paleta de colores**:
- Background: `#0B0D10` (casi negro)
- Surface: `#14171C` (gris oscuro)
- Primary: `#F5A623` (dorado)
- Secondary: `#22C55E` (verde éxito)
- Text Primary: `#FFFFFF`
- Text Secondary: `#B0B3B8`
- Text Muted: `#6B6F76`

**Tipografía**:
- Font: Inter (sans-serif)
- Headings: 600 weight
- Body: 400 weight
- Numeric values: 500 weight para datos

---

## 3. Estructura de Layout

**Tipo**: Sidebar + Top Navigation

**Sidebar** (260px, izquierda, collapsible):
- Logo + Brand
- Navigation items con iconos
- Settings al final

**Topbar** (64px, sticky):
- Breadcrumb / Page title
- Search
- Notifications
- User avatar
- Theme toggle

**Content Area**:
- Grid de 12 columnas
- Gap: 24px
- Padding: 24px

**Responsive**:
- Mobile: Sidebar como drawer, single column
- Tablet: 2-3 columnas
- Desktop: Full layout 12 columnas

---

## 4. Componentes

### KPI Cards (4 tarjetas en row)
1. **Total Balance**: $124,592.45 (+12.5%)
2. **Portfolio Value**: $98,230.18 (+8.3%)
3. **24h Volume**: $2.4M (-2.1%)
4. **Active Trades**: 18 (+5)

Cada tarjeta incluye:
- Icono (Wallet, TrendingUp, BarChart3, Activity)
- Título
- Valor principal (grande, bold)
- Trend indicator (porcentaje + flecha)
- Color de acento según tipo

### Chart: Portfolio Performance
- Tipo: Area chart
- Datos: 6 meses históricos
- Eje Y: Valor en USD
- Eje X: Fechas (mensual)
- Fill con gradiente (primary a transparent)
- Tooltip con valor exacto

### Chart: Asset Distribution
- Tipo: Pie/Donut chart
- Datos: 4 categorías (BTC, ETH, SOL, Others)
- Colores: Primary, Blue, Green, Muted
- Legend al lado o abajo

### Table: Recent Trades
Columnas:
- Asset (icon + nombre)
- Type (badge: Buy/Sell)
- Amount (cantidad)
- Price (precio unitario)
- Total (precio × cantidad)
- Time (fecha/hora relativa)

Features:
- Pagination (10 items por página)
- Sorting por columna
- Hover highlight

---

## 5. Datos Mock

### Portfolio History
```javascript
[
  { date: "2024-01", value: 82000 },
  { date: "2024-02", value: 85000 },
  { date: "2024-03", value: 91000 },
  { date: "2024-04", value: 88200 },
  { date: "2024-05", value: 96000 },
  { date: "2024-06", value: 98230 }
]
```

### Asset Distribution
```javascript
[
  { name: "Bitcoin", value: 45 },
  { name: "Ethereum", value: 30 },
  { name: "Solana", value: 15 },
  { name: "Others", value: 10 }
]
```

### Recent Trades
```javascript
[
  { asset: "BTC", type: "buy", amount: 0.5, price: 45230, total: 22615, time: "2 min ago" },
  { asset: "ETH", type: "sell", amount: 4.2, price: 3120, total: 13104, time: "15 min ago" },
  // ... más items
]
```

---

## 6. Interacciones

### Hover States
- Cards: Slight elevation increase, shadow grow
- Table rows: Background highlight
- Buttons: Opacity/color change
- Nav items: Background pill highlight

### Animations
- Cards: Fade in + slide up on load
- Charts: Draw animation on mount
- Numbers: Count up animation for KPIs
- Transitions: 300ms ease

### Theme Toggle
- Switch entre dark/light
- Smooth transition (no flash)
- Persistencia en localStorage

---

## Design Tokens Reference

Ver archivo: `design-brief-fintech.jsonc`

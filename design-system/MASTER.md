---
project: FreakingJSON Dashboard SPA
version: 1.0.0
date: 2026-03-04
---

# Design System Master
## FreakingJSON Dashboard SPA

---

## 1. BRAND IDENTITY

### Logo & Name
- **Name**: FreakingJSON
- **Tagline**: "Tu Asistente AI Personal. Tu Conocimiento. Tu Control."
- **Frase Insignia**: "El conocimiento verdadero trasciende a lo público"

### Brand Values
- Local-first: Todo en tus archivos
- Privacy-first: Sin credenciales expuestas
- MVI: Minimal Viable Information
- Multi-CLI: Universal y agnóstico

---

## 2. COLOR SYSTEM

### Primary Colors
```css
--color-primary: #0EA5E9;          /* Sky 500 - Fresh tech blue */
--color-primary-dark: #0284C7;     /* Sky 600 - Hover states */
--color-primary-light: #38BDF8;    /* Sky 400 - Accents */
```

### Secondary Colors
```css
--color-secondary: #8B5CF6;        /* Violet 500 - Creative purple */
--color-secondary-dark: #7C3AED;   /* Violet 600 */
--color-secondary-light: #A78BFA;  /* Violet 400 */
```

### Neutral Colors (Dark Mode Default)
```css
/* Backgrounds */
--bg-primary: #0F172A;             /* Slate 900 - Main bg */
--bg-secondary: #1E293B;           /* Slate 800 - Cards */
--bg-tertiary: #334155;            /* Slate 700 - Elevated */
--bg-quaternary: #475569;          /* Slate 600 - Borders */

/* Text */
--text-primary: #F8FAFC;           /* Slate 50 - Headings */
--text-secondary: #CBD5E1;         /* Slate 300 - Body */
--text-tertiary: #94A3B8;          /* Slate 400 - Muted */
--text-disabled: #64748B;          /* Slate 500 - Disabled */

/* Semantic */
--color-success: #22C55E;          /* Green 500 */
--color-warning: #EAB308;          /* Yellow 500 */
--color-error: #EF4444;            /* Red 500 */
--color-info: #3B82F6;             /* Blue 500 */
```

### Accent Colors for Features
```css
--accent-release: #10B981;         /* Emerald 500 */
--accent-bugfix: #F59E0B;          /* Amber 500 */
--accent-research: #EC4899;        /* Pink 500 */
--accent-features: #8B5CF6;        /* Violet 500 */
```

---

## 3. TYPOGRAPHY

### Font Family
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
```

### Type Scale
```css
/* Headings */
--text-h1: 2.5rem;      /* 40px - Hero titles */
--text-h2: 2rem;        /* 32px - Section titles */
--text-h3: 1.5rem;      /* 24px - Card titles */
--text-h4: 1.25rem;     /* 20px - Subsection */
--text-h5: 1rem;        /* 16px - Labels */

/* Body */
--text-body: 1rem;      /* 16px - Default */
--text-small: 0.875rem; /* 14px - Secondary */
--text-xs: 0.75rem;     /* 12px - Captions */

/* Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

---

## 4. SPACING SYSTEM

### Scale (rem-based)
```css
--space-0: 0;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

### Layout
```css
--container-max: 1400px;
--sidebar-width: 280px;
--sidebar-collapsed: 64px;
--header-height: 64px;
--chat-input-height: 80px;
```

---

## 5. COMPONENT LIBRARY

### Buttons

#### Primary Button
```css
.btn-primary {
  background: var(--color-primary);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.2s;
}
.btn-primary:hover {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}
```

#### Secondary Button
```css
.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--bg-quaternary);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.2s;
}
.btn-secondary:hover {
  background: var(--bg-quaternary);
}
```

#### Ghost Button
```css
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  transition: all 0.2s;
}
.btn-ghost:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
```

### Cards

#### Default Card
```css
.card {
  background: var(--bg-secondary);
  border: 1px solid var(--bg-quaternary);
  border-radius: 0.75rem;
  padding: 1.5rem;
  transition: all 0.2s;
}
.card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
```

#### Interactive Card (Session)
```css
.card-session {
  background: var(--bg-secondary);
  border-left: 3px solid transparent;
  border-radius: 0.5rem;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.15s;
}
.card-session:hover {
  background: var(--bg-tertiary);
  border-left-color: var(--color-primary);
}
.card-session.active {
  background: var(--bg-tertiary);
  border-left-color: var(--color-primary);
}
```

### Input Fields

#### Search Input
```css
.input-search {
  background: var(--bg-tertiary);
  border: 1px solid var(--bg-quaternary);
  border-radius: 9999px;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  color: var(--text-primary);
  width: 100%;
  transition: all 0.2s;
}
.input-search:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}
.input-search::placeholder {
  color: var(--text-tertiary);
}
```

### Navigation

#### Sidebar Navigation
```css
.sidebar {
  background: var(--bg-secondary);
  border-right: 1px solid var(--bg-quaternary);
  width: var(--sidebar-width);
  height: 100vh;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: var(--text-secondary);
  border-radius: 0.375rem;
  margin: 0 0.5rem;
  transition: all 0.15s;
}
.nav-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
.nav-item.active {
  background: var(--color-primary);
  color: white;
}
```

#### Top Navigation
```css
.top-nav {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--bg-quaternary);
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
}
```

### Chat/Message Components

#### Message Bubble - Agent
```css
.message-agent {
  background: var(--bg-tertiary);
  border: 1px solid var(--bg-quaternary);
  border-radius: 1rem 1rem 1rem 0.25rem;
  padding: 1rem;
  margin-left: 0;
  margin-right: 3rem;
}
.message-agent::before {
  content: "🤖";
  margin-right: 0.5rem;
}
```

#### Message Bubble - User
```css
.message-user {
  background: var(--color-primary);
  color: white;
  border-radius: 1rem 1rem 0.25rem 1rem;
  padding: 1rem;
  margin-left: 3rem;
  margin-right: 0;
}
.message-user::before {
  content: "👤";
  margin-right: 0.5rem;
}
```

#### Warning Banner
```css
.banner-warning {
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid var(--color-warning);
  border-radius: 0.5rem;
  padding: 1rem;
  color: var(--color-warning);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.banner-warning::before {
  content: "⚠️";
}
```

---

## 6. LAYOUT PATTERNS

### Dashboard Layout (ChatGPT-like)
```
┌────────────────────────────────────────────────────────┐
│ Header (fixed)                                          │
├──────────────┬─────────────────────────────────────────┤
│              │                                         │
│   Sidebar    │         Main Content Area               │
│   (fixed)    │         (scrollable)                    │
│              │                                         │
│              │                                         │
│              │                                         │
├──────────────┴─────────────────────────────────────────┤
│ Input Area (fixed at bottom when needed)               │
└────────────────────────────────────────────────────────┘
```

CSS:
```css
.layout-dashboard {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  grid-template-rows: var(--header-height) 1fr;
  grid-template-areas:
    "header header"
    "sidebar main";
  height: 100vh;
  overflow: hidden;
}
```

### Mobile Layout
```css
@media (max-width: 768px) {
  .layout-dashboard {
    grid-template-columns: 1fr;
    grid-template-areas:
      "header"
      "main";
  }
  .sidebar {
    position: fixed;
    left: -100%;
    transition: left 0.3s;
  }
  .sidebar.open {
    left: 0;
  }
}
```

---

## 7. ANIMATIONS & INTERACTIONS

### Transitions
```css
--transition-fast: 150ms ease;
--transition-normal: 200ms ease;
--transition-slow: 300ms ease;
```

### Hover Effects
```css
.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.hover-glow:hover {
  box-shadow: 0 0 20px rgba(14, 165, 233, 0.3);
}
```

### Loading States
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.loading {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skeleton {
  background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-quaternary) 50%, var(--bg-tertiary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

---

## 8. ICONOGRAPHY

### Icon Style
- Style: Outline (Heroicons)
- Size: 20px (default), 24px (navigation)
- Color: Inherit from text

### Common Icons
```
Home: 🏠 or <HomeIcon />
Chat: 💬 or <ChatBubbleLeftIcon />
Search: 🔍 or <MagnifyingGlassIcon />
Settings: ⚙️ or <CogIcon />
User: 👤 or <UserIcon />
Menu: ☰ or <Bars3Icon />
Close: ✕ or <XMarkIcon />
Arrow: → or <ArrowRightIcon />
External Link: ↗ or <ArrowTopRightOnSquareIcon />
```

---

## 9. ACCESSIBILITY

### Color Contrast
- All text meets WCAG 2.1 AA (4.5:1 for normal, 3:1 for large)
- Interactive elements have visible focus states

### Focus States
```css
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 10. PAGE-SPECIFIC OVERRIDES

### Dashboard Page
```css
/* pages/dashboard.css */
.dashboard-hero {
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

.dashboard-stat-card {
  border-top: 3px solid var(--color-primary);
}
```

### Chat Page
```css
/* pages/chat.css */
.chat-sidebar {
  background: var(--bg-primary);
}

.chat-message-area {
  background: var(--bg-primary);
  background-image: radial-gradient(var(--bg-tertiary) 1px, transparent 1px);
  background-size: 20px 20px;
}
```

---

## 11. ANTI-PATTERNS

### ❌ Don't
- Use pure black (#000) or pure white (#fff)
- Use more than 3 font weights
- Make interactive elements smaller than 44px touch target
- Use low contrast text
- Animate layout properties (width, height, top, left)

### ✅ Do
- Use the neutral color scale for backgrounds
- Keep animations to transform and opacity
- Use semantic HTML elements
- Provide focus states for keyboard navigation
- Test with actual content, not just lorem ipsum

---

*Design System generated for FreakingJSON Dashboard SPA*
*Following @ui-ux-pro-max standards*

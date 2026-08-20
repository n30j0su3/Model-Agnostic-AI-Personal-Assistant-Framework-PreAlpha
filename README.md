<p align="center">
  <img src="assets/hero-pa-prealpha.png" alt="FreakingJSON PA Framework — Command Center local-first" width="880">
</p>

# FreakingJSON PA Framework

**Tu Asistente AI Personal. Tu Conocimiento. Tu Control.**

[![Version](https://img.shields.io/badge/version-vv0.4.1-beta)]()
[![Python](https://mod-rect.vercel.app/Python.svg)]( 3.11%2B)
[![License](https://img.shields.io/badge/license-MIT-lime)]()

Framework **local-first y model-agnostic** para operar un asistente de IA personal desde tu propia máquina: sin nube obligatoria, sin suscripciones, sin que tus datos salgan de tu carpeta.

> *"I own my context. Nothing annoys me more than when AI tries to fence me in, give me vendor lock-in. No, I reject that."*
> — La filosofía de este framework, inspirada en NetworkChuck

---

## Características del Framework / Harness

| Módulo | Estado |
|---|---|
| Menú CLI (`pa.bat` / `pa.sh`) | ✅ Operativo |
| Dashboard visual (`dashboard.html`) — SPA offline, single-file | ✅ Operativo |
| Documentación completa offline (8 guías ES/EN, embebidas) | ✅ Operativo |
| **Índice de skills automático** (en cada arranque + installer) | ✅ Nuevo vv0.4.1-beta |
| **Métricas reales de uso** (sin datos demo/falsos) | ✅ Nuevo vv0.4.1-beta |
| Sesiones opencode (listar/reanudar) | ✅ Operativo |
| Chat con IA (puente local) | ✅ Operativo |
| **Selector + configuración de modelos free** (opencode) | ✅ Operativo |
| Consola/Chat del dashboard (puente local) | 🚧 Oculto (v0.5+) |
| Desinstalación | 🚧 Deprecado (v0.5+) |

### El harness en 30 segundos

- **Arranque**: `pa.bat` / `pa.sh` → validación, auto-heal, migraciones, **índice de skills** e **índice de interacciones** regenerados en cada arranque.
- **Dashboard**: `dashboard.html` funciona sin servidor (modo lectura) o con puente local (`dashboard_server.py`) para chat/consola/modelos.
- **Memoria persistente**: sesiones en `core/.context/sessions/`, skills en `core/skills/`, índices de conocimiento en `core/.context/knowledge/` — todo local, todo tuyo.
- **Model-agnostic**: cualquier proveedor configurado en `.opencode/config.json` (ej. `opencode/big-pickle`, NanoGPT free models).
- **Modelo free**: opción `M` del menú o página **Modelo** del dashboard para detectar y configurar los modelos free disponibles vía opencode.
- **Docs bilingües**: pestaña 📚 Documentación — 8 guías completas en ES/EN con toggle de idioma, tablas y listas renderizadas, todo offline.

## Inicio rápido (no técnico)

### Windows
1. Descarga y extrae el ZIP en una carpeta.
2. Doble clic en **`pa.bat`** — instala Python/opencode si faltan (via winget/npm) y abre el menú.
3. Opción **`5`** → Iniciar Sesión IA. Listo.

### macOS / Linux
```bash
./pa.sh
```

### Dashboard visual
Abre **`dashboard.html`** en tu navegador. Funciona sin servidor ni dependencias (modo lectura). Para Chat/Modelos, inicia el puente local:
```bash
python core/scripts/dashboard_server.py
```
y recarga — el dashboard detecta el puente automáticamente.

## Requisitos
- Python 3.11+
- [opencode](https://opencode.ai) CLI (auto-instalable en Windows)

## Estructura
```
pa-framework/
├── pa.bat / pa.sh          # Entrada principal (menú interactivo)
├── dashboard.html          # Dashboard visual + documentación bilingüe
└── core/
    ├── scripts/            # Lógica del framework (Python stdlib)
    ├── skills/             # Skills recargables (indexadas al arranque)
    └── .context/           # Memoria local (no trackeada)
```

## Documentación
- **Dashboard** → pestaña **📚 Documentación** (todo incluido, ES/EN, offline)
- **CLI** → `pa.bat` → opción `7` (Ayuda)
- Este README + `docs/` (fuente de la documentación)

## Versiones
Ver `CHANGELOG.md`. Versión actual: **vv0.4.1-beta**.

## Licencia
MIT — ver `LICENSE`.

---

## 🙏 Agradecimientos

Gracias a Dios por la Gracia, la Revelación y el Discernimiento necesarios para construir este framework.

Gracias a mi familia por su amor y paciencia, y a todos mis seres queridos (ellos saben quiénes son).

Un agradecimiento especial a **[NetworkChuck](https://www.youtube.com/@NetworkChuck)** por inspirar la filosofía central de este proyecto:

> *"I own my context. Nothing annoys me more than when AI tries to fence me in, give me vendor lock-in. No, I reject that."*

Su enfoque de soberanía de datos y aprendizaje accesible fue fundamental para el diseño de este framework.

---

Hecho con ❤️ por **FreakingJSON**.

### 🔗 Conecta con FreakingJSON

- 📸 **Instagram**: [@freakingjson](https://instagram.com/freakingjson)
- 🌐 **Todas las redes**: [linktr.ee/freakingjson](https://linktr.ee/freakingjson)
- 📝 **Blog Tech & Homelab**: [freakingjson.com](https://freakingjson.com)
- ☕ **Apoya el proyecto**: [buymeacoffee.com/freakingjson](https://buymeacoffee.com/freakingjson)

> *"I own my context. I am FreakingJSON."*
>
> **"El conocimiento verdadero trasciende a lo público."**

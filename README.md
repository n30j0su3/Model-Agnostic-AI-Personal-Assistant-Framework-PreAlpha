# FreakingJSON PA Framework

**Tu Asistente AI Personal. Tu Conocimiento. Tu Control.**

[![Version](https://img.shields.io/badge/version-v0.4.0--beta-lime)]()
[![Python](https://mod-rect.vercel.app/Python.svg)]( 3.11%2B)
[![License](https://img.shields.io/badge/license-MIT-lime)]()

Framework local-first y model-agnostic para operar un asistente de IA personal desde tu propia máquina: sin nube obligatoria, sin suscripciones, sin que tus datos salgan de tu carpeta.

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
Abre **`dashboard.html`** en tu navegador. Funciona sin servidor ni dependencias (modo lectura). Para Consola/Chat/Modelos, inicia el puente local:
```bash
python core/scripts/dashboard_server.py
```
y recarga — el dashboard detecta el puente automáticamente.

## Qué hace

| Módulo | Estado |
|---|---|
| Menú CLI (`pa.bat` / `pa.sh`) | ✅ Operativo |
| Dashboard visual (`dashboard.html`) | ✅ Operativo (docs incluidas) |
| Documentación completa offline | ✅ Pestaña 📚 Documentación |
| Sesiones opencode (listar/reanudar) | ✅ Operativo |
| Chat con IA (puente local) | ✅ Operativo |
| Selector de modelos free | ✅ Operativo |
| Desinstalación | 🚧 Deprecado (v0.5+) |

## Requisitos
- Python 3.11+
- [opencode](https://opencode.ai) CLI (auto-instalable en Windows)

## Estructura

```
pa-framework/
├── pa.bat / pa.sh          # Entrada principal (menú interactivo)
├── dashboard.html          # Dashboard visual + documentación incluida
└── core/
    ├── scripts/            # Lógica del framework (Python stdlib)
    ├── skills/             # Skills recargables
    └── .context/           # Memoria local (no trackeada)
```

## Documentación
- **Dashboard** → pestaña **📚 Documentación** (todo incluido, offline)
- **CLI** → `pa.bat` → opción `7` (Ayuda)
- Este README + `docs/` (fuente de la documentación)

## Versiones
Ver `CHANGELOG.md`. Versión actual: **v0.4.0-beta**.

## Licencia
MIT — ver `LICENSE`.

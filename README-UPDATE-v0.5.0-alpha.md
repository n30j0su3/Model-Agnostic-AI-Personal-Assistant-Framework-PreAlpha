# PA Framework — README de Actualización v0.5.0-alpha

> **Versión**: v0.5.0-alpha (2026-08-15)  
> **Estado**: Release acumulativo con fixes críticos + nuevas capacidades

---

## 🚀 Cambios Críticos v0.5.0-alpha

### 1. Fix: opencode inicia en modo "FreakingJSON" (no "Build")

**Problema**: opencode 1.4.6+ usa "Build" como modo default cuando no se especifica `--agent`.

**Solución**: `pa.py` ahora pasa explícitamente `--agent FreakingJSON` al lanzar opencode.

```python
# core/scripts/pa.py:build_cli_command()
return [cli, "--agent", "FreakingJSON"] + model_flag + ["--prompt", prompt], True
```

**Verificación**: al ejecutar `pa.bat` → opción 6 (Iniciar Sesión IA), opencode debe mostrar "FreakingJSON" como agente activo.

---

### 2. Selección de Modelo Free

**Problema**: opencode usa el modelo default de su config global (ej. "Big Pickle"), que puede no ser free o puede consumir créditos.

**Solución**: 
- Nuevo script `core/scripts/select_free_model.py` consulta `opencode serve` y lista modelos free disponibles.
- Menú interactivo: opción 3 (Comportamiento Agente) → tecla `M` → selecciona modelo free y guarda en `.opencode/config.json`.
- `pa.py` lee el modelo desde config y lo pasa vía `--model`.

**Uso**:
```bash
python core/scripts/pa.py
# 3 → Comportamiento Agente → M → Seleccionar modelo free
```

**Config resultante** (`.opencode/config.json`):
```json
{
  "agent": "FreakingJSON",
  "model": "minimax/minimax-m2.1-free"
}
```

---

### 3. Workspaces Correctos

**Problema**: el agente creaba entregables en `workspaces/content/SPA-HTML-*` en lugar de `workspaces/content/projects/`.

**Solución**: `.opencode/agent/FreakingJSON.md` ahora incluye regla de workspace:

```markdown
<rule id="workspace_structure">
  TODO entregable DEBE crearse en `workspaces/content/projects/NOMBRE_PROYECTO/`.
  NUNCA crear directamente en `workspaces/content/SPA-HTML-*` fuera de projects.
</rule>
```

---

### 4. Persistencia de Preferencias de Usuario

**Problema**: preferencias como "me gusta el neon y turquesa" no se guardaban en MASTER.md.

**Solución**: FreakingJSON.md incluye regla `persist_preferences`:

```markdown
<rule id="persist_preferences">
  Cuando el usuario exprese preferencias (colores, estilo, framework, etc.),
  PERSISTIR inmediatamente en `core/.context/MASTER.md` bajo sección "Preferencias".
</rule>
```

**Ejemplo**:
```
Usuario: "me gusta el neon y turquesa"
→ Agente agrega a MASTER.md:
   ## Preferencias
   - Colores: neon, turquesa
   - Estilo: cyberpunk, futurista
```

---

### 5. Desinstalador Interactivo

**Nuevo script**: `core/scripts/uninstall.py`

**Características**:
- Opcional: eliminar datos personales (MASTER.md, sessions/, knowledge/)
- Elimina cache SQLite
- Opcional: desinstalar opencode global (afecta otros proyectos)
- Opcional: eliminar scripts del framework (deja repo git limpio)

**Uso**:
```bash
python core/scripts/uninstall.py
```

---

### 6. Compatibilidad macOS

**Nuevo script**: `core/scripts/check_mac_compat.py`

**Verifica**:
- Python versión
- opencode instalado (brew o npm)
- npm / Homebrew disponibles
- Paths críticos (~/.opencode, /opt/homebrew/bin, etc.)

**Uso**:
```bash
python core/scripts/check_mac_compat.py
```

---

## 📦 Instalación / Actualización

### Fresh Install (Windows)
```bash
# Descargar ZIP
curl -L https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/archive/v0.5.0-alpha.zip -o PA-Framework-v0.5.0-alpha.zip

# Extraer
tar -xf PA-Framework-v0.5.0-alpha.zip

# Iniciar
cd Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha-0.5.0-alpha
.\pa.bat
```

### Actualización desde v0.4.0-beta
```bash
cd tu-repo-pa-framework
git pull origin main
git tag -f v0.5.0-alpha
python core/scripts/session_start.py  # auto-heal + migraciones
```

---

## 🔧 Dependencias

### Requeridas
- **Python 3.10+** (stdlib puro, sin dependencias externas)
- **opencode 1.4.6+** (vía npm: `npm install -g opencode-ai`)

### Opcionales (para features avanzadas)
- **Node.js 18+** (para opencode)
- **Homebrew** (macOS, para instalar opencode: `brew install opencode`)
- **Git** (para actualizaciones)

**¿Por qué zero-dependencias?**
- El framework corre en cualquier máquina con Python instalado
- Sin `pip install`, sin venv, sin conflicts de versiones
- Los scripts usan solo stdlib: `subprocess`, `json`, `pathlib`, `urllib`, `socket`

---

## 🏗️ Filosofía del Framework

### Local-First
- Todo el conocimiento se guarda en archivos `.md` locales
- SQLite para sesiones (consultas rápidas)
- Sin cloud, sin APIs externas (excepto opencode como CLI local)

### Modelo-Agnostic
- Soporta opencode, Claude Code, Gemini CLI, Codex CLI
- El usuario elige su modelo preferido (free o pago)
- El framework no impone ningún proveedor

### Zero-Config
- Fresh install funciona sin configuración manual
- Auto-heal regenera archivos faltantes desde seeds
- Migraciones automáticas entre versiones

### Privacy-First
- Credenciales como variables de entorno o placeholders `[REDACTED]`
- Datos personales opcionales (MASTER.md, profile.md)
- Desinstalador preserva datos si el usuario quiere

---

## 📚 Estructura de Archivos Clave

```
pa-framework/
├── core/
│   ├── scripts/
│   │   ├── pa.py                    # Menú interactivo principal
│   │   ├── session_start.py         # Auto-heal + migraciones
│   │   ├── select_free_model.py     # v0.5.0: selección modelo free
│   │   ├── uninstall.py             # v0.5.0: desinstalador
│   │   └── check_mac_compat.py      # v0.5.0: compat macOS
│   ├── .context/
│   │   ├── MASTER.md                # Config global + preferencias usuario
│   │   ├── profile.md               # Perfil de instalación
│   │   └── sessions/                # Sesiones diarias (YYYY-MM-DD.md)
│   └── agents/
│       └── FreakingJSON.md          # Agente principal (reglas, workflow)
├── .opencode/
│   ├── config.json                  # Agent + modelo default
│   └── agent/
│       └── FreakingJSON.md          # Definición de agente opencode
├── workspaces/
│   └── content/
│       └── projects/                # ← ENTREGABLES AQUÍ
├── dashboard.html                   # SPA dashboard (chat, sesiones, config)
├── pa.bat / pa.sh                   # Launchers
└── VERSION                          # v0.5.0-alpha
```

---

## 🎯 Ejemplos de Uso

### 1. Iniciar Sesión IA con Modelo Free
```bash
python core/scripts/pa.py
# 3 → Comportamiento Agente → M → Seleccionar modelo free
# 6 → Iniciar Sesión IA → opencode (con --agent FreakingJSON --model <free>)
```

### 2. Crear Proyecto Nuevo
```bash
# Desde el menú:
# 1 → Workspaces → Crear nuevo → "mi-proyecto"

# El agente creará:
# workspaces/content/projects/mi-proyecto/
```

### 3. Guardar Preferencias
```
Usuario: "prefiero colores oscuros, neon verde y turquesa"
Agente: (automáticamente guarda en MASTER.md)
```

### 4. Desinstalar
```bash
python core/scripts/uninstall.py
# ¿Eliminar datos personales? N (preservar)
# ¿Eliminar cache? Y
# ¿Desinstalar opencode? N (es global)
# ¿Eliminar scripts? N (dejar repo)
```

---

## 🧪 Testing / QA

### Fresh Install
```bash
/tmp/pa-fresh/
└── extraer ZIP
└── python core/scripts/session_start.py  # 0 errores
└── python core/scripts/pa.py --help      # funciona
└── python -m pytest tests/ -q            # 54/54 passed
```

### Windows cp1252
```bash
# Simular consola Windows
PYTHONIOENCODING=cp1252 PYTHONUTF8=0 python core/scripts/pa.py --help
# Debe imprimir sin "I/O operation on closed file" ni "lost sys.stderr"
```

---

## 📝 Changelog Completo

Ver `CHANGELOG.md` para el historial detallado.

**Resumen v0.5.0-alpha**:
- Fix crítico: opencode modo FreakingJSON
- Selección de modelo free
- Reglas de workspace y persistencia
- Desinstalador + macOS compat
- Docs actualizadas

---

## 🤝 Contribución

1. Fork del repo
2. Crear rama feature (`git checkout -b feature/nueva-capacidad`)
3. Commit cambios (`git commit -m 'feat: nueva capacidad'`)
4. Push (`git push origin feature/nueva-capacidad`)
5. PR a `main`

---

## 📞 Soporte

- **GitHub Issues**: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/issues
- **Documentación**: `README.md`, `AGENTS.md`, `core/.context/quick-start.md`
- **Dashboard**: `http://localhost:8760` (tras ejecutar `dashboard_server.py`)

---

*Framework creado por FreakingJSON — "El conocimiento verdadero trasciende a lo público"*

# Guía de Uso: Framework con Gemini CLI

> Cómo usar el Model-Agnostic AI Personal Assistant Framework con **Gemini CLI**

---

## 🚀 Instalación Rápida

### Requisitos
- **Gemini CLI** instalado: https://github.com/google-gemini/gemini-cli
- **Python 3.11+**
- **Git** (opcional pero recomendado)

### Paso 1: Descargar el Framework
```bash
# Con Git
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha.git

# O descarga el ZIP desde Releases
```

### Paso 2: Configurar Gemini CLI
```bash
# Inicia sesión con tu cuenta Google
gemini login

# Verifica que funciona
gemini --version
```

### Paso 3: Instalar el Framework
```bash
cd Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha
python3 core/scripts/install.py
```

Durante la instalación, selecciona **Gemini** como tu CLI principal.

---

## 🎯 Uso Básico

### Iniciar una Sesión

```bash
# Opción A: Usar el launcher del framework
./pa.sh        # macOS/Linux
pa.bat         # Windows

# Opción B: Directamente con Gemini
gemini
```

### Flujo de Trabajo Típico

1. **Iniciar sesión del día**:
   ```bash
   ./pa.sh
   # Selecciona "Iniciar Sesión AI"
   ```

2. **Trabajar con el agente**:
   - El framework carga automáticamente tu contexto
   - Usa comandos como `/status`, `/session`, `/help`
   - El agente FreakingJSON-PA te guiará

3. **Finalizar sesión**:
   - Todo el contexto se guarda automáticamente
   - Revisa tu sesión en `core/.context/sessions/`

---

## ⚡ Comandos Útiles

| Comando | Descripción |
|---------|-------------|
| `./pa.sh` | Menú principal del framework |
| `gemini` | Iniciar Gemini CLI directamente |
| `gemini --help` | Ayuda de Gemini CLI |
| `./pa.sh --status` | Ver estado del framework |

---

## 🔧 Configuración Avanzada

### Variables de Entorno (opcional)
```bash
# macOS/Linux - agrega a ~/.bashrc o ~/.zshrc
export GEMINI_API_KEY="tu-api-key"

# Windows PowerShell
setx GEMINI_API_KEY "tu-api-key"
```

### Configurar Modelo
Por defecto, Gemini CLI usa el modelo más reciente. Puedes especificar:
```bash
# Usar Gemini 2.5 Pro
gemini --model gemini-2.5-pro

# Ver modelos disponibles
gemini models list
```

---

## 📚 Recursos del Framework

- **Dashboard SPA**: Abre `dashboard.html` en tu navegador
- **Documentación**: Ver `docs/PHILOSOPHY.md` y `docs/WORKFLOW-STANDARD.md`
- **Skills disponibles**: Ver `core/skills/SKILLS.md`
- **Changelog**: Ver `CHANGELOG.md`

---

## ❓ Troubleshooting

**"Gemini command not found"**
→ Asegúrate de que Gemini CLI esté instalado y en tu PATH

**"No se detecta el contexto del framework"**
→ Ejecuta `./pa.sh` primero para inicializar el entorno

**"Error de permisos en pa.sh"**
→ Ejecuta: `chmod +x pa.sh`

---

## 🌐 Recursos Externos

- **Gemini CLI Docs**: https://github.com/google-gemini/gemini-cli
- **Framework Releases**: https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/releases
- **Reportar Issues**: Usa GitHub Issues en el repositorio

---

> **Nota**: Esta es una guía específica para usuarios de Gemini CLI. El framework también funciona con OpenCode, Claude Code, y otras herramientas.

---

*Framework versión: v0.2.1-prealpha*  
*Última actualización: 2026-03-05*

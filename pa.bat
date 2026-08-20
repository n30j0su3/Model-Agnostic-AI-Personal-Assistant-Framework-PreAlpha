@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"
chcp 65001 >nul

:: ===========================================================================
:: PA FRAMEWORK - Inicio rapido para Windows
:: ===========================================================================
:: Creado por: FreakingJSON | instagram.com/freakingjson
:: Version: 0.4.1-beta
:: ===========================================================================

:: --- Ayuda rapida (no necesita instalacion) ---
if /i "%1"=="/?" goto :show_help
if /i "%1"=="/help" goto :show_help
if /i "%1"=="-h" goto :show_help
if /i "%1"=="--help" goto :show_help
if /i "%1"=="/version" goto :show_version

:: ------------------------------------------------------------
:: 1) Ensure Python (auto-install via winget when possible)
:: ------------------------------------------------------------
set "PY_CMD="
call :detect_python

if not defined PY_CMD (
  echo [WARN] Python not found. Trying automatic install...
  call :install_python_auto
  call :detect_python
)

if not defined PY_CMD (
  echo [ERROR] Python is required and could not be installed automatically.
  echo [INFO] Install manually: https://www.python.org/downloads/
  pause
  exit /b 1
)

echo [OK] Python detected: !PY_CMD!

:: ------------------------------------------------------------
:: 2) First run installer
:: ------------------------------------------------------------
if not exist "core\.context\profile.md" (
  echo [INFO] First run detected. Running installer...
  !PY_CMD! core\scripts\install.py
  if !errorlevel! neq 0 (
    echo [ERROR] Installation failed.
    pause
    exit /b !errorlevel!
  )
)

:: ------------------------------------------------------------
:: 3) Ensure OpenCode (auto-install)
:: ------------------------------------------------------------
where opencode >nul 2>nul
if errorlevel 1 (
  echo [WARN] OpenCode not found. Trying automatic install...
  call :install_opencode_auto
)

where opencode >nul 2>nul
if errorlevel 1 (
  echo [WARN] OpenCode still not detected. You can install it manually:
  echo [INFO] npm install -g opencode-ai
) else (
  echo [OK] OpenCode detected.
)

:: ------------------------------------------------------------
:: 4) Launch framework
:: ------------------------------------------------------------
!PY_CMD! core\scripts\pa.py %*
exit /b %errorlevel%

:: ===========================================================================
:: HELP - Ayuda para usuarios no tecnicos
:: ===========================================================================
:show_help
echo.
echo ============================================================
echo   FreakingJSON PA Framework - Guia Rapida v0.4.1-beta
echo ============================================================
echo.
echo  QUE ES ESTO?
echo   Es un asistente de IA personal que funciona en tu PC.
echo   No necesita internet (solo para los modelos de IA en nube).
echo   Todo queda en tus archivos locales.
echo.
echo  COMO USAR:
echo   Solo ejecuta:  pa.bat
echo   El menu te guiara paso a paso. No sabes programar? No importa.
echo.
echo  PRIMERA VEZ:
echo   1. Te preguntara por tu idioma preferido
echo   2. Elegiras que herramienta de IA usar (OpenCode, Claude, etc.)
echo   3. Y listo! Ya puedes empezar
echo.
echo  COMANDOS RAPIDOS:
echo   pa.bat                    - Menu interactivo (recomendado)
echo   pa.bat --cli opencode     - Inicia OpenCode directamente (flujo base)
echo                             : validacion + init del framework + TUI opencode
echo   pa.bat --sync             - Sincroniza configuracion
echo   pa.bat /help              - Esta ayuda
echo   pa.bat /version           - Version del framework
echo.
echo  NECESITAS AYUDA?
echo   - Revisa README.md (el archivo de documentacion incluido)
echo   - Instagram: @freakingjson
echo.
echo  "I own my context. I am FreakingJSON."
echo.
goto :eof


:: ===========================================================================
:: VERSION
:: ===========================================================================
:show_version
if exist VERSION (
  set /p VERSION_CONTENT=<VERSION
  echo FreakingJSON PA Framework v%VERSION_CONTENT%
) else (
  echo FreakingJSON PA Framework v%VERSION_CONTENT%
)
goto :eof

:: ===========================================================================
:: Python detection
:: ===========================================================================
:detect_python
set "PY_CMD="
python -V >nul 2>nul
if %errorlevel%==0 set "PY_CMD=python"
if not defined PY_CMD (
  py -3 -V >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=py -3"
)
goto :eof

:: ===========================================================================
:: Auto-install Python via winget
:: ===========================================================================
:install_python_auto
where winget >nul 2>nul
if errorlevel 1 (
  echo [WARN] winget not available. Cannot auto-install Python.
  goto :eof
)

echo [INFO] Installing Python 3.11 via winget (user scope)...
winget install -e --id Python.Python.3.11 --scope user --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
  echo [WARN] winget Python install failed.
) else (
  echo [OK] Python install command completed.
)
goto :eof

:: ===========================================================================
:: Auto-install OpenCode
:: ===========================================================================
:install_opencode_auto
:: Try npm first
where npm >nul 2>nul
if not errorlevel 1 (
  echo [INFO] Installing OpenCode via npm...
  call npm install -g opencode-ai
  if not errorlevel 1 goto :eof
  echo [WARN] npm install failed.
)

:: If npm missing, try Node.js via winget then retry npm
where winget >nul 2>nul
if errorlevel 1 (
  echo [WARN] winget not available. Cannot auto-install Node.js/OpenCode.
  goto :eof
)

echo [INFO] Installing Node.js LTS via winget...
winget install -e --id OpenJS.NodeJS.LTS --scope user --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
  echo [WARN] Node.js install failed.
  goto :eof
)

echo [INFO] Retrying OpenCode install via npm...
call npm install -g opencode-ai
goto :eof

@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"
chcp 65001 >nul

echo [INFO] Starting PA Framework bootstrap...

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

:detect_python
set "PY_CMD="
python -V >nul 2>nul
if %errorlevel%==0 set "PY_CMD=python"
if not defined PY_CMD (
  py -3 -V >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=py -3"
)
goto :eof

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

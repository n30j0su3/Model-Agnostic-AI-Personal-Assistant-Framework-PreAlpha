@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"
chcp 65001 >nul

:: Detect Python
set "PY_CMD="
python -V >nul 2>nul
if %errorlevel%==0 set "PY_CMD=python"
if not defined PY_CMD (
  py -3 -V >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=py -3"
)

if not defined PY_CMD (
  echo [ERROR] Python no encontrado. Es obligatorio.
  echo [INFO] Descarga: https://www.python.org/downloads/
  pause
  exit /b 1
)

:: Auto-install if profile missing
if not exist "core\.context\profile.md" (
  echo [INFO] Primera ejecucion detectada. Iniciando instalador...
  %PY_CMD% core\scripts\install.py
  if !errorlevel! neq 0 (
    echo [ERROR] Instalacion incompleta.
    pause
    exit /b !errorlevel!
  )
)

:: Delegate to main Python script
%PY_CMD% core\scripts\pa.py %*
exit /b %errorlevel%
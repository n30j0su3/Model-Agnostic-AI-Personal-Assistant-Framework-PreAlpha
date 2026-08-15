@echo off
REM FreakingJSON PA Framework — Dashboard Launcher (Windows)
REM Doble-click para iniciar el dashboard con auto-configuración

echo.
echo ===============================================
echo   FreakingJSON PA Framework
echo   Dashboard Launcher v0.5.0-alpha
echo ===============================================
echo.

REM Verificar Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no detectado.
    echo Instala Python 3.10+ desde https://python.org
    pause
    exit /b 1
)

REM Verificar opencode
where opencode >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if exist "%USERPROFILE%\.opencode\bin\opencode.exe" (
        set "OPENCODE_PATH=%USERPROFILE%\.opencode\bin"
        set "PATH=%OPENCODE_PATH%;%PATH%"
    ) else (
        echo [WARNING] opencode no detectado.
        echo Para usar chat con IA, instala: npm install -g opencode-ai
        echo.
        set /p INSTALL="¿Instalar opencode ahora? (Y/N): "
        if /i "%INSTALL%"=="Y" (
            echo Instalando opencode...
            call npm install -g opencode-ai
        )
    )
)

REM Iniciar launcher
echo Iniciando dashboard...
python "%~dp0core\scripts\dashboard_launcher.py"

pause

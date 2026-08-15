@echo off
REM FreakingJSON PA Framework — Dashboard Launcher (Windows)
REM Doble-click para iniciar el dashboard con auto-configuración
REM Uso: dashboard-launcher.bat [/uninstall]

cd /d "%~dp0"

if /i "%1"=="/uninstall" goto :run_uninstall

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
goto :eof

:run_uninstall
echo.
echo ===============================================
echo   PA Framework - Desinstalador
echo ===============================================
echo.
python core\scripts\uninstall.py
goto :eof

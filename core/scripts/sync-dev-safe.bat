@echo off
REM Script de Sync Seguro para DEV con protección de recursos críticos
REM Este script hace backup manual de recursos protegidos antes del sync

echo ==========================================
echo SYNC SEGURO DEV - Con proteccion Maaji
echo ==========================================

set BASE_DIR=C:\ACTUAL\FreakingJSON-pa\Model-Agnostic-AI-Personal-Assistant-Framework
set DEV_DIR=C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV
set BACKUP_DIR=%DEV_DIR%\.sync-backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%

echo.
echo [1/5] Creando backups de recursos protegidos...
echo     Backup dir: %BACKUP_DIR%

mkdir "%BACKUP_DIR%" 2>nul

REM Backup agentes locales
if exist "%DEV_DIR%\core\agents\subagents\_local" (
    echo     [OK] Backup agentes locales
    xcopy /E /I /H /Y "%DEV_DIR%\core\agents\subagents\_local" "%BACKUP_DIR%\agents\_local" >nul
)

REM Backup skills locales
if exist "%DEV_DIR%\core\skills\_local" (
    echo     [OK] Backup skills locales
    xcopy /E /I /H /Y "%DEV_DIR%\core\skills\_local" "%BACKUP_DIR%\skills\_local" >nul
)

REM Backup workspaces
if exist "%DEV_DIR%\workspaces" (
    echo     [OK] Backup workspaces
    xcopy /E /I /H /Y "%DEV_DIR%\workspaces" "%BACKUP_DIR%\workspaces" >nul
)

REM Backup contexto workspaces
if exist "%DEV_DIR%\core\.context\workspaces" (
    echo     [OK] Backup contexto workspaces
    xcopy /E /I /H /Y "%DEV_DIR%\core\.context\workspaces" "%BACKUP_DIR%\context\workspaces" >nul
)

REM Backup docs específicos
if exist "%DEV_DIR%\docs\MAAJI-PROMOTION-GUIDE.md" (
    echo     [OK] Backup docs específicos
    copy /Y "%DEV_DIR%\docs\MAAJI-PROMOTION-GUIDE.md" "%BACKUP_DIR%\" >nul
)

echo.
echo [2/5] Ejecutando sync con script optimizado...
cd /d "%BASE_DIR%"

REM Ejecutar sync (el backup de directorios protegidos está en el script)
python core\scripts\sync-prealpha-optimized.py --mode=dev --verbose

echo.
echo [3/5] Verificando recursos protegidos post-sync...

set RECURSOS_OK=1

if not exist "%DEV_DIR%\core\agents\subagents\_local\maaji\maaji-master.md" (
    echo     [RESTAURANDO] Agente maaji-master
    xcopy /E /I /H /Y "%BACKUP_DIR%\agents\_local" "%DEV_DIR%\core\agents\subagents\_local" >nul
    set RECURSOS_OK=0
)

if not exist "%DEV_DIR%\core\skills\_local\maaji\atribucion\SKILL.md" (
    echo     [RESTAURANDO] Skills Maaji
    xcopy /E /I /H /Y "%BACKUP_DIR%\skills\_local" "%DEV_DIR%\core\skills\_local" >nul
    set RECURSOS_OK=0
)

if not exist "%DEV_DIR%\workspaces\professional\projects\Maaji" (
    echo     [RESTAURANDO] Workspaces
    xcopy /E /I /H /Y "%BACKUP_DIR%\workspaces" "%DEV_DIR%\workspaces" >nul
    set RECURSOS_OK=0
)

if not exist "%DEV_DIR%\docs\MAAJI-PROMOTION-GUIDE.md" (
    echo     [RESTAURANDO] Docs específicos
    copy /Y "%BACKUP_DIR%\MAAJI-PROMOTION-GUIDE.md" "%DEV_DIR%\docs\" >nul
    set RECURSOS_OK=0
)

if %RECURSOS_OK%==1 (
    echo     [OK] Todos los recursos protegidos están presentes
)

echo.
echo [4/5] Verificando que dashboard-pro llegó...
if exist "%DEV_DIR%\core\skills\core\dashboard-pro\skill.yaml" (
    echo     [OK] dashboard-pro/skill.yaml presente
) else (
    echo     [ERROR] dashboard-pro NO encontrado
)

echo.
echo [5/5] Limpieza...
echo     Backup preservado en: %BACKUP_DIR%
echo     (Eliminar manualmente cuando se confirme todo OK)

echo.
echo ==========================================
echo SYNC COMPLETADO
echo ==========================================
echo.
echo Proximos pasos:
echo   1. Verificar cambios: cd %DEV_DIR% ^&^& git status
echo   2. Revisar recursos protegidos
echo   3. Si todo OK: git add . ^&^& git commit
echo.

pause

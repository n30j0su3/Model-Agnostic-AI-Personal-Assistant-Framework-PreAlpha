@echo off
REM Sistema de Sincronización para Windows
REM Framework FreakingJSON-PA - PreAlpha

echo ========================================
echo    Sistema de Sync - FreakingJSON-PA
echo ========================================
echo.
echo Selecciona la operacion:
echo.
echo 1. BASE -^> DEV (Traer mejoras del framework)
echo 2. DEV -^> BASE (Sincronizar feature a framework)
echo 3. BASE -^> PROD (Publicar version limpia)
echo 4. Validacion de seguridad
echo.
echo 0. Salir
echo.

set /p opcion="Opcion: "

if "%opcion%"=="1" goto base_to_dev
if "%opcion%"=="2" goto dev_to_base
if "%opcion%"=="3" goto base_to_prod
if "%opcion%"=="4" goto validar
if "%opcion%"=="0" exit

echo Opcion invalida
pause
exit

:base_to_dev
echo.
echo [INFO] Ejecutando: sync-base-to-dev.sh
echo.
REM Buscar Git Bash o WSL
if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" -c "cd '%CD%' && ./core/scripts/sync-base-to-dev.sh"
) else (
    echo [ERROR] Git Bash no encontrado
    echo Instala Git para Windows desde: https://git-scm.com/download/win
)
pause
exit

:dev_to_base
echo.
echo [INFO] Ejecutando: sync-dev-to-base.sh
echo.
if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" -c "cd '%CD%' && ./core/scripts/sync-dev-to-base.sh"
) else (
    echo [ERROR] Git Bash no encontrado
)
pause
exit

:base_to_prod
echo.
echo [INFO] Ejecutando: sync-base-to-prod.sh
echo.
echo [ADVERTENCIA] Esto publicara a un repositorio PUBLICO
echo.
set /p confirmar="Escribe PUBLICAR para continuar: "
if not "%confirmar%"=="PUBLICAR" (
    echo Cancelado
    pause
    exit
)
if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" -c "cd '%CD%' && ./core/scripts/sync-base-to-prod.sh"
) else (
    echo [ERROR] Git Bash no encontrado
)
pause
exit

:validar
echo.
echo [INFO] Ejecutando: validate-sync-safety.sh
echo.
if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" -c "cd '%CD%' && ./core/scripts/validate-sync-safety.sh"
) else (
    echo [ERROR] Git Bash no encontrado
)
pause
exit

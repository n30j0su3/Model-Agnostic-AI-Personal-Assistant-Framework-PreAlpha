@echo off
REM Backup Manual de Recursos Críticos
REM Ejecutar ANTES de cualquier sync importante

echo ============================================
echo BACKUP DE RECURSOS CRITICOS
echo ============================================
echo.

set BACKUP_DIR=C:\ACTUAL\FreakingJSON-pa\Model-Agnostic-AI-Personal-Assistant-Framework\bk
set DEV_DIR=C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV

echo [1/3] Creando directorio de backup...
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo.
echo [2/3] Copiando _local/agents...
xcopy /E /I /H /Y "%DEV_DIR%\core\agents\subagents\_local" "%BACKUP_DIR%\core\agents\subagents\_local" >nul
if %errorlevel%==0 (
    echo   [OK] Agentes locales copiados
) else (
    echo   [ERROR] Fallo copia de agentes
)

echo.
echo [3/3] Copiando _local/skills...
xcopy /E /I /H /Y "%DEV_DIR%\core\skills\_local" "%BACKUP_DIR%\core\skills\_local" >nul
if %errorlevel%==0 (
    echo   [OK] Skills locales copiados
) else (
    echo   [ERROR] Fallo copia de skills
)

echo.
echo ============================================
echo BACKUP COMPLETADO
echo Ubicacion: %BACKUP_DIR%
echo ============================================
echo.
pause

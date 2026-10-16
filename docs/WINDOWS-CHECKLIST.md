# Windows x64 QA Checklist — PA Framework v0.4.1-beta

**Estado:** candidato local pendiente de QA humana en Windows x64
**Runtime requerido:** Python 3.11+
**Default:** OpenCode
**Alternativa opt-in:** Pi

> Ejecuta este protocolo sobre una extracción nueva del ZIP cuyo SHA-256 haya
> reportado el responsable del release. No reutilices carpetas de pruebas
> anteriores.

---

## 1. Identidad del artefacto

En PowerShell, desde la carpeta que contiene el ZIP:

```powershell
Get-FileHash .\pa-framework-0.4.1-beta.zip -Algorithm SHA256
```

Registra:

- SHA-256 observado.
- Edición y versión de Windows.
- Arquitectura (`$env:PROCESSOR_ARCHITECTURE` debe ser `AMD64`).
- Salida de `py -3.11 --version`.

**FAIL inmediato:** el hash no coincide, la arquitectura no es AMD64 o no hay
Python 3.11+.

---

## 2. Extracción limpia

1. Elimina o aparta extracciones anteriores.
2. Extrae el ZIP en una ruta nueva y corta, por ejemplo:
   `C:\PA-QA\pa-framework-0.4.1-beta`.
3. Abre PowerShell dentro de esa carpeta.
4. Confirma que existe `MANIFEST.sha256.json`.

No copies dentro del candidato perfiles, sesiones ni archivos `data/` de una
instalación anterior durante los smokes iniciales.

---

## 3. Smokes no destructivos

```powershell
cmd /c pa.bat --help
cmd /c pa.bat /version
py -3.11 core\scripts\install.py --non-interactive --dry-run --json --no-browser
```

Esperado:

- Los tres comandos terminan con exit code `0`.
- `/version` muestra una sola `v`: `v0.4.1-beta`.
- El JSON del dry-run contiene:
  - `"ok": true`
  - `"mode": "dry-run"`
  - `"version": "0.4.1-beta"`
  - `"writes": []`
- El dry-run no crea perfil, token ni datos de usuario.

---

## 4. Suite automatizada Windows

Si `pytest` no está disponible, instálalo únicamente en un entorno virtual de QA:

```powershell
py -3.11 -m venv .qa-venv
.\.qa-venv\Scripts\Activate.ps1
python -m pip install pytest
python -m pytest tests -q
```

Esperado:

- Cero fallos.
- El test visual CDP puede aparecer como `skipped` si no se configuró un browser
  remoto; se prueba manualmente en la sección 6.
- Al terminar, `git status` no aplica dentro del ZIP porque el paquete no incluye
  `.git`; valida en cambio que no aparezcan archivos inesperados fuera de
  `.qa-venv`, `data/` o caches locales.

La carpeta `.qa-venv` es solo de QA y no forma parte del producto.

---

## 5. Instalación y wizard

Sobre otra extracción limpia, ejecuta:

```powershell
py -3.11 core\scripts\install.py --non-interactive --json --no-browser
```

Luego prueba el flujo humano con:

```powershell
cmd /c pa.bat
```

Validar:

- OpenCode sigue preseleccionado por defecto.
- Pi solo se activa si el usuario lo elige explícitamente.
- Cancelar o no disponer de credenciales no inventa un estado autenticado.
- La selección de runtime/modelo se guarda bajo `data\user\`.
- No se modifica `.opencode\config` como efecto secundario de selección.
- Los textos y acentos se muestran correctamente en consola UTF-8.

No compartas API keys, tokens ni contenido de `data\user\` en el reporte.

---

## 6. Dashboard en navegador

```powershell
py -3.11 core\scripts\dashboard_server.py --host 127.0.0.1 --port 8765
```

Abre `http://127.0.0.1:8765/` y valida:

- La página carga sin 4xx visibles.
- La versión visible es `v0.4.1-beta` y coincide con `/api/status`.
- Home, workflow, docs y footer muestran una única versión canónica.
- La sección Docs abre contenido no vacío.
- El selector de idioma de Docs persiste tras recargar.
- No hay overflow horizontal a 360, 480, 768 y 1600 px.
- Botones/enlaces principales tienen un área táctil utilizable.
- La consola del navegador no muestra errores JavaScript.

Detén el servidor con `Ctrl+C` al terminar.

---

## 7. Migración v0.4.0 → v0.4.1 y rollback

Usa una **copia descartable** de una instalación v0.4.0; nunca la única copia de
los datos del usuario.

```powershell
py -3.11 core\scripts\migrate.py --check
py -3.11 core\scripts\migrate.py --apply
py -3.11 core\scripts\migrate.py --apply
py -3.11 core\scripts\migrate.py --status
```

Validar:

- El primer apply crea un snapshot en `data\rollback\`.
- El segundo apply es idempotente y no duplica la migración.
- Perfil, sesiones y datos del usuario siguen presentes.

Rollback, usando la ruta exacta del snapshot generado:

```powershell
py -3.11 core\scripts\rollback.py --snapshot data\rollback\<snapshot>.tar.gz --json
```

Validar que las superficies administradas regresan al estado anterior y que los
datos personales no se borran.

---

## 8. Resultado que debe reportarse

```text
Windows: <edición/build>
Arquitectura: AMD64
Python: <versión>
ZIP SHA-256: <hash>
Smokes pa.bat: PASS/FAIL
Installer dry-run: PASS/FAIL
Suite pytest: <passed/skipped/failed>
Wizard OpenCode default: PASS/FAIL
Pi opt-in: PASS/FAIL/NOT TESTED
Dashboard: PASS/FAIL
Migración doble: PASS/FAIL/NOT TESTED
Rollback: PASS/FAIL/NOT TESTED
Hallazgos: <pasos exactos + mensaje de error, sin secretos>
Veredicto: PASS / BLOCKED
```

Un `FAIL` o una prueba crítica `NOT TESTED` mantiene la publicación en **NO-GO**.
No crear tag ni release desde el equipo Windows de QA.

# Guía de migración — PA Framework v0.4.1-beta

**Para usuarios que vienen de versiones anteriores.**
Versión destino: `v0.4.1-beta` · Fecha: 2026-10-18 · Licencia: MIT

---

## Guía rápida de migración

> **Regla de oro:** el backup seguro no se toca. Nunca ejecutes el framework, migraciones ni scripts dentro del backup; restaura siempre desde una **copia** del backup.

1. **Backup limpio.** Detén el framework y guarda solo lo importante: `core/.context/`, `data/user/`, `data/sessions.db`, `data/user_memory.db`, `workspaces/`, `config/`, `.opencode/config.json` y `opencode.jsonc`. Verifica que la copia contiene tus archivos. No incluyas `node_modules/`, `.pytest_cache/` ni `__pycache__/`.
2. **Elige una ruta:**
   - **Menú de `pa.bat` / `pa.sh`:** usa la opción de **Buscar actualizaciones**. El updater crea snapshot y restaura el estado protegido. Ideal si tu instalación actual está sana.
   - **Copia limpia del ZIP del repo (recomendado):** extrae `v0.4.1-beta` en una carpeta **nueva**, nunca encima de la vieja. Ideal si hay dudas, forks o si el update falla.
3. **Restaura desde una copia del backup**, no desde el backup original. Copia a la instalación nueva o actualizada:
   - `core/.context/` (MASTER, profile, sessions, codebase, knowledge, memory)
   - `data/user/`, `data/sessions.db`, `data/user_memory.db`
   - `workspaces/`
   - `config/mcp.json`, `config/quotas.json`, `.opencode/config.json`, `opencode.jsonc`
   - No copies `node_modules/`, `.pytest_cache/`, `__pycache__/` ni scripts viejos.
   - Puedes hacerlo **manualmente** o con la opción de **importación/restauración del propio framework**, si tu versión la ofrece.
4. **Verifica.** `VERSION`, `python core/scripts/system_check.py --quick`, `python core/scripts/migrate.py --check`, perfil, workspaces, sesiones y modelo.
5. **Si algo falla.** Usa el snapshot del updater con `rollback.py` o vuelve a extraer el ZIP limpio y restaura otra copia del backup. No borres el backup original.

---

## 1. Antes de empezar

Detén el dashboard, OpenCode y cualquier sesión del framework. Trabaja desde la raíz de tu instalación actual.

### Backup obligatorio

Copia estas rutas a un lugar seguro:

```text
core/.context/
data/
workspaces/
config/
.opencode/config.json
opencode.jsonc
```

**Windows PowerShell:**

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force ".\backup-$stamp" | Out-Null
Copy-Item core\.context ".\backup-$stamp\core-context" -Recurse
Copy-Item data ".\backup-$stamp\data" -Recurse
Copy-Item workspaces ".\backup-$stamp\workspaces" -Recurse
Copy-Item config ".\backup-$stamp\config" -Recurse
Copy-Item .opencode\config.json ".\backup-$stamp\opencode-config.json"
Copy-Item opencode.jsonc ".\backup-$stamp\opencode.jsonc"
```

**macOS / Linux:**

```bash
stamp=$(date +%Y%m%d-%H%M%S)
mkdir -p "backup-$stamp"
cp -a core/.context "backup-$stamp/core-context"
cp -a data "backup-$stamp/data"
cp -a workspaces "backup-$stamp/workspaces"
cp -a config "backup-$stamp/config"
cp -a .opencode/config.json "backup-$stamp/opencode-config.json"
cp -a opencode.jsonc "backup-$stamp/opencode.jsonc"
```

No necesitas backup de `node_modules`, `.pytest_cache` ni `__pycache__`.

### Comprueba tu versión actual

**Windows:**

```powershell
Get-Content .\VERSION
py -3.11 --version
opencode --version
```

**macOS / Linux:**

```bash
cat VERSION
python3 --version
opencode --version
```

Requisitos de destino: **Python 3.11+** y **OpenCode >= 1.18.0**.

Si OpenCode es anterior:

```bash
npm install -g opencode-ai@latest
opencode --version
```

---

## 2. Elige tu ruta

### Ruta A — v0.4.0-beta → v0.4.1-beta (recomendada, automática)

Es el camino soportado y probado. El updater crea snapshots y restaura el estado protegido.

1. Comprueba si hay actualización:

```bash
python core/scripts/update.py --check
```

2. Aplica:

```bash
python core/scripts/update.py
```

3. Verifica:

```bash
python core/scripts/system_check.py --quick
python core/scripts/kb_init.py --check
python core/scripts/migrate.py --check
```

4. Si hay migraciones pendientes:

```bash
python core/scripts/migrate.py --apply
```

5. Arranca y revisa tu perfil, workspaces, sesiones y modelo:

```bash
pa.bat        # Windows
./pa.sh       # macOS/Linux
```

### Ruta B — v0.3.x → v0.4.1-beta (automática con verificación)

Puedes intentar el mismo `update.py`, pero v0.3.x tiene más superficie histórica. Después de actualizar, **revisa migraciones y datos** antes de confiar en la instalación.

1. Backup completo (sección 1).
2. `python core/scripts/update.py --check`.
3. `python core/scripts/update.py`.
4. `python core/scripts/migrate.py --status` y `--check`.
5. Si hay pendientes: `python core/scripts/migrate.py --apply`.
6. `python core/scripts/system_check.py --quick`.
7. `python core/scripts/kb_init.py --check`.
8. Abre el framework y confirma:
   - `core/.context/MASTER.md` y `profile.md` existen.
   - Tus workspaces siguen en `config/workspaces.json` y en disco.
   - Tus sesiones siguen en `core/.context/sessions/`.
   - Tu modelo/credencial sigue disponible.

Si el update falla, no completa o tu instalación tiene cambios locales fuertes, usa la **Ruta C**.

### Ruta C — v0.2.x o anterior, o update fallido (instalación limpia + restauración)

Las migraciones automáticas cubren estructuras del framework, no todas las personalizaciones antiguas. La ruta segura es una instalación limpia y restaurar tus datos.

1. Backup completo (sección 1).
2. Extrae `v0.4.1-beta` en una carpeta **nueva** (no encima de la vieja).
3. Copia desde tu backup a la carpeta nueva:
   - `core/.context/MASTER.md`
   - `core/.context/profile.md`
   - `core/.context/sessions/`
   - `core/.context/codebase/`
   - `core/.context/knowledge/insights/`
   - `core/.context/knowledge/learning/`
   - `core/.context/knowledge/prompts/`
   - `core/.context/memory/`
   - `data/user/`
   - `data/sessions.db`
   - `data/user_memory.db`
   - `workspaces/`
   - `config/mcp.json`
   - `config/quotas.json`
   - `.opencode/config.json`
   - `opencode.jsonc`
4. **No copies** `node_modules/`, `.pytest_cache/`, `__pycache__/`, scripts viejos ni `data/backups/` completos.
5. Aplica migraciones:

```bash
python core/scripts/migrate.py --check
python core/scripts/migrate.py --apply
```

6. Verifica:

```bash
python core/scripts/system_check.py --quick
python core/scripts/kb_init.py --check
```

7. Arranca con `pa.bat`/`pa.sh` y revisa el estado.

### Ruta D — fork o instalación muy personalizada

No sobrescribas tu fork con el ZIP. Haz merge manual de los cambios de v0.4.1-beta y conserva tus rutas. Como mínimo, adopta:

- `config/update-protected-paths.txt` add-only.
- Migraciones `[KEEP]`.
- `pa.sh` LF/100755 y flags informativos.
- Contrato OpenCode `>=1.18.0`.
- Manifest schema 2 si usas el builder público.

---

## 3. Qué cambia en v0.4.1-beta

- **Protección de datos add-only.** `config/update-protected-paths.txt` puede sumar rutas, pero no quitar los defaults. Si antes habías eliminado un default, ahora vuelve a estar protegido; tus rutas adicionales se conservan.
- **Migraciones `[KEEP]`.** Si un archivo ya existe, la migración no lo sobrescribe. Esto protege backlog, índices, configuración y archivos personalizados.
- **`workspaces/content` legacy se conserva.** Si tu selección ya no lo incluye, el instalador no lo borra: te informa su ruta.
- **Cold start veraz.** El receipt guarda el storage real (SQLite, Wiki, MD memory, sesiones).
- **Consola cp1252.** Los scripts programados y launchers manejan UTF-8; no deberían abortar en Windows legacy.
- **Launcher POSIX.** `pa.sh` viaja en LF, ejecutable, y responde `--help`/`--version` antes del instalador.
- **OpenCode runtime-managed.** El gate exige `>=1.18.0`. `.opencode/package.json` y `package-lock.json` se incluyen para el bootstrap, pero el CLI puede reescribirlos; se validan por contrato semver, no por hash.
- **Manifest schema 2.** El ZIP certifica 385 archivos y declara 2 runtime-managed. No afecta a tu instalación; afecta a la verificación del paquete.

## 4. Qué NO cambia

- Tus datos siguen en `core/.context/`, `data/` y `workspaces/`.
- No hay migración a la nube ni telemetría.
- No se borran sesiones, perfiles, workspaces ni credenciales.
- No se cambia el formato de las sesiones `.md`.
- No se incluye ningún modelo ni credencial en el paquete.

---

## 5. Verificación post-migración

Marca cada punto:

- [ ] `VERSION` muestra `0.4.1-beta`.
- [ ] `python core/scripts/system_check.py --quick` termina sin errores críticos.
- [ ] `python core/scripts/kb_init.py --check` OK.
- [ ] `python core/scripts/migrate.py --check` sin pendientes.
- [ ] `core/.context/MASTER.md` y `profile.md` existen.
- [ ] Tus workspaces siguen en `config/workspaces.json` y en disco.
- [ ] Tus sesiones siguen en `core/.context/sessions/`.
- [ ] Tu modelo/credencial sigue disponible.
- [ ] `pa.bat` o `./pa.sh` abre el menú.
- [ ] El dashboard abre.
- [ ] `warm-start.json` muestra el storage real.

---

## 6. Rollback

Si algo sale mal, usa el snapshot exacto que reportó el updater o el migrator:

```bash
python core/scripts/rollback.py --snapshot data/backups/pre-migration-<timestamp> --json
```

**Windows:**

```powershell
py -3.11 core\scripts\rollback.py --snapshot data\backups\pre-migration-<timestamp> --json
```

El rollback restaura las superficies administradas por el framework y conserva el estado protegido del usuario. Si el receipt no contiene `"ok": true`, detente y conserva el snapshot para diagnóstico. **No borres** `data/backups/` ni `.update-preservation/`.

---

## 7. Problemas frecuentes

### “Framework actualizado” pero sigo en la versión vieja

Revisa `VERSION` y que estés ejecutando el `update.py` de la instalación correcta. `--force` solo salta el chequeo de versión igual; no salta snapshots ni validaciones.

### El update no descarga

El updater exige TLS verificado. Si tu red lo bloquea, descarga el ZIP oficial, verifica el SHA-256 y usa la Ruta C (instalación limpia + restauración). No desactives la verificación TLS.

### `migrate.py --check` reporta pendientes

```bash
python core/scripts/migrate.py --apply
```

Si falla, conserva el snapshot y revisa el mensaje. No edites `.migration_state.json` a mano.

### OpenCode anterior a 1.18.0

```bash
npm install -g opencode-ai@latest
opencode --version
```

### `pa.sh: Permission denied`

```bash
chmod +x pa.sh
./pa.sh
```

### “No such file or directory: profile.md”

```bash
python core/scripts/system_check.py --fix --quiet-first-run
```

### No veo mis workspaces

Revisa `config/workspaces.json` y `core/.context/MASTER.md`. Si el directorio existe pero no está listado, añádelo desde el menú de configuración; no borres `workspaces/content` a mano.

### La consola muestra caracteres raros

```powershell
chcp 65001
```

Los launchers ya activan UTF-8; esto es solo para terminales antiguas.

---

## 8. Notas para Windows

- Usa una ruta corta, por ejemplo `C:\PA`.
- Evita `Program Files`, `OneDrive` y rutas con acentos.
- Ejecuta `py -3.11` si `python` apunta a otra versión.
- No necesitas Developer Mode.
- Si SmartScreen bloquea `pa.bat`, verifica el SHA-256 antes de elegir **Ejecutar de todas formas**.

---

## 9. Soporte

- **Issues:** https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/issues
- **Web:** https://freakingjson.com
- **Guía de instalación:** `GUIA-DE-INSTALACION-v0.4.1-beta.md`
- **Update guide general:** `docs/UPDATE-GUIDE.md`

Al reportar, incluye versión de origen, versión destino, sistema operativo, comando exacto y mensaje de error. **No incluyas** rutas personales, tokens ni contenido de tus sesiones.

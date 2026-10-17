# Update Guide / Guía de actualización

This guide describes the supported update and rollback flow for PA Framework.
Esta guía describe el flujo soportado de actualización y rollback de PA Framework.

## 1. Before updating / Antes de actualizar

Run every command from the framework root. Keep the framework stopped while the
update is applied.

Ejecuta todos los comandos desde la raíz del framework. Mantén el framework
detenido mientras se aplica la actualización.

```bash
python core/scripts/update.py --check
```

`--check` only compares versions; it does not write framework or user files.
`--check` solo compara versiones; no escribe archivos del framework ni del usuario.

## 2. Protected user state / Estado de usuario protegido

The updater preserves the paths declared in `config/update-protected-paths.txt`,
including:

- `workspaces`
- `data/user`
- `data/sessions.db`
- `data/user_memory.db`
- user context under `core/.context/`
- user-owned model and quota configuration

El actualizador preserva esas mismas superficies antes de copiar o restaurar
archivos del framework.

## 3. Apply the update / Aplicar la actualización

```bash
python core/scripts/update.py
```

Before changing framework files, the updater must create:

- a rollback-compatible snapshot under `data/backups/pre-migration-<timestamp>/`;
- a protected-state backup under `data/backups/update-protected-<timestamp>/`.

The update fails closed if the snapshot, verified HTTPS download, archive safety
validation, migration, protected-state restore, or Knowledge Base initialization
fails. `--force` only bypasses the equal-version check; it does not bypass the
snapshot or safety gates.

Antes de modificar el framework, el actualizador crea el snapshot y el backup
anteriores. Cualquier fallo de seguridad o preservación cancela la actualización
con exit code distinto de cero.

## 4. Verify / Verificar

```bash
python core/scripts/system_check.py --quick
python core/scripts/kb_init.py --check
```

Confirm that your profile, workspaces, sessions and model selection remain
available. Do not publish logs or files under `data/user` as QA evidence.

Confirma que tu perfil, workspaces, sesiones y selección de modelo siguen
disponibles. No publiques logs ni archivos de `data/user` como evidencia de QA.

## 5. Roll back / Revertir

Use the exact snapshot directory reported by the updater or migrator:

```bash
python core/scripts/rollback.py --snapshot data/backups/pre-migration-<timestamp> --json
```

Rollback restores framework-managed surfaces while preserving protected user
state. A successful JSON receipt contains `"ok": true`; otherwise stop and keep
the snapshot directory intact for diagnosis.

El rollback restaura superficies administradas por el framework y conserva el
estado protegido del usuario. Si el receipt JSON no contiene `"ok": true`, detén
el proceso y conserva el snapshot para diagnóstico.

## 6. Windows notes / Notas para Windows

Use Python 3.11+ and an extraction with a short path. In PowerShell the same
rollback target can be written as:

```powershell
py -3.11 core\scripts\rollback.py --snapshot data\backups\pre-migration-<timestamp> --json
```

Run the native checklist in `docs/WINDOWS-CHECKLIST.md` against the exact release
ZIP and SHA-256 supplied for human QA.

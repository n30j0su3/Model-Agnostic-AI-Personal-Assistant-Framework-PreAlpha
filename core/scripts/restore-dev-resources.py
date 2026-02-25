import shutil
import os
from pathlib import Path

print("=" * 60)
print("RESTAURACIÓN DE RECURSOS PROTEGIDOS - DEV")
print("=" * 60)

# Rutas
BACKUP_DIR = Path(
    r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV\.sync-backup-20260224"
)
DEV_DIR = Path(r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV")

# Recursos a restaurar
resources = [
    ("agents/_local", "core/agents/subagents/_local"),
    ("skills/_local", "core/skills/_local"),
    ("workspaces", "workspaces"),
    ("MAAJI-PROMOTION-GUIDE.md", "docs/MAAJI-PROMOTION-GUIDE.md"),
]

restored = 0
failed = 0

for backup_rel, dev_rel in resources:
    backup_path = BACKUP_DIR / backup_rel
    dev_path = DEV_DIR / dev_rel

    if not backup_path.exists():
        print(f"[SKIP] No en backup: {backup_rel}")
        continue

    try:
        # Eliminar versión actual si existe
        if dev_path.exists():
            if dev_path.is_dir():
                shutil.rmtree(dev_path)
            else:
                dev_path.unlink()

        # Restaurar desde backup
        if backup_path.is_dir():
            shutil.copytree(backup_path, dev_path)
            print(f"[✓] RESTAURADO (dir): {dev_rel}")
        else:
            # Asegurar que el directorio padre existe
            dev_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, dev_path)
            print(f"[✓] RESTAURADO (file): {dev_rel}")

        restored += 1
    except Exception as e:
        print(f"[✗] ERROR restaurando {dev_rel}: {e}")
        failed += 1

print("=" * 60)
print(f"RESULTADO: {restored} restaurados, {failed} fallidos")
print("=" * 60)

import shutil
import os
from pathlib import Path

BACKUP_DIR = Path(
    r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV\.sync-backup-20260224"
)
DEV_DIR = Path(r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV")

print("[RESTAURACION] Recursos protegidos desde backup...")

# Restaurar agentes locales
src = BACKUP_DIR / "agents" / "_local"
dst = DEV_DIR / "core" / "agents" / "subagents" / "_local"
if src.exists():
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"  [OK] Agentes locales: {dst}")

# Restaurar skills locales
src = BACKUP_DIR / "skills" / "_local"
dst = DEV_DIR / "core" / "skills" / "_local"
if src.exists():
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"  [OK] Skills locales: {dst}")

# Restaurar docs
src = BACKUP_DIR / "MAAJI-PROMOTION-GUIDE.md"
dst = DEV_DIR / "docs" / "MAAJI-PROMOTION-GUIDE.md"
if src.exists():
    shutil.copy2(src, dst)
    print(f"  [OK] Docs: {dst}")

print("[OK] Restauracion completada")

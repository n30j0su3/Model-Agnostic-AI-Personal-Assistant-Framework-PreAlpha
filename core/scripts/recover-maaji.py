import shutil
from pathlib import Path

print("=" * 60)
print("[FASE 1] RECUPERANDO MAAJI DESDE bk/")
print("=" * 60)

# Rutas
BK_DIR = Path(
    r"C:\ACTUAL\FreakingJSON-pa\Model-Agnostic-AI-Personal-Assistant-Framework\bk"
)
DEV_DIR = Path(r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV")

# 1. Recuperar agente maaji-master
print("\n[1/2] Recuperando agente maaji-master...")
src = BK_DIR / "core" / "agents" / "subagents" / "_local" / "maaji"
dst = DEV_DIR / "core" / "agents" / "subagents" / "_local" / "maaji"

if src.exists():
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"  [OK] Copiado: {src} -> {dst}")
else:
    print(f"  [ERROR] No encontrado: {src}")

# 2. Recuperar skills Maaji
print("\n[2/2] Recuperando skills Maaji...")
src = BK_DIR / "core" / "skills" / "_local" / "maaji"
dst = DEV_DIR / "core" / "skills" / "_local" / "maaji"

if src.exists():
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"  [OK] Copiado: {src} -> {dst}")
else:
    print(f"  [ERROR] No encontrado: {src}")

# 3. Verificación
print("\n" + "=" * 60)
print("[VERIFICACIÓN] Archivos recuperados:")
print("=" * 60)

files_to_check = [
    DEV_DIR / "core" / "agents" / "subagents" / "_local" / "maaji" / "maaji-master.md",
    DEV_DIR / "core" / "skills" / "_local" / "maaji" / "atribucion" / "SKILL.md",
    DEV_DIR
    / "core"
    / "skills"
    / "_local"
    / "maaji"
    / "checkout-con-evento"
    / "SKILL.md",
    DEV_DIR
    / "core"
    / "skills"
    / "_local"
    / "maaji"
    / "checkout-sin-evento"
    / "SKILL.md",
    DEV_DIR / "core" / "skills" / "_local" / "maaji" / "klaviyo-extract" / "SKILL.md",
]

all_present = True
for f in files_to_check:
    if f.exists():
        size = f.stat().st_size
        print(f"  [OK] {f.name}: {size} bytes")
    else:
        print(f"  [FALTA] {f}")
        all_present = False

print("\n" + "=" * 60)
if all_present:
    print("[OK] FASE 1 COMPLETADA - Todos los archivos recuperados")
else:
    print("[ERROR] Algunos archivos faltan")
print("=" * 60)

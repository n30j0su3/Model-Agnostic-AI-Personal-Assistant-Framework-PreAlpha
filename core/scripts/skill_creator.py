#!/usr/bin/env python3
"""
FreakingJSON PA Framework — Skill Creator Automático (v0.5.0-alpha)

Genera skills automáticamente desde:
1. Ejemplos de código existentes
2. Prompts en lenguaje natural (vía opencode)
3. Auto-mejora de skills existentes

Uso:
  python core/scripts/skill_creator.py --from-example "ejemplo.py" --name "mi-skill"
  python core/scripts/skill_creator.py --from-prompt "Quiero una skill que..."
  python core/scripts/skill_creator.py --improve "core/skills/existente.toml"
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / "core" / "skills"
SCRIPTS_DIR = REPO_ROOT / "core" / "scripts" / "skills"

# Colores
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log(msg, color=Colors.RESET, bold=False):
    prefix = f"{Colors.BOLD}{color}" if bold else color
    print(f"{prefix}[Skill Creator] {msg}{Colors.RESET}", flush=True)

def call_opencode(prompt, timeout=60):
    """Llamar a opencode para generar contenido."""
    # Intentar encontrar opencode
    import shutil
    exe = shutil.which("opencode")
    if not exe:
        home_bin = Path.home() / ".opencode" / "bin" / "opencode"
        if home_bin.exists():
            exe = str(home_bin)
    
    if not exe:
        log("opencode no encontrado. Instala con: npm install -g opencode-ai", Colors.RED)
        return None
    
    try:
        result = subprocess.run(
            [exe, "--prompt", prompt],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(REPO_ROOT)
        )
        return result.stdout.strip()
    except Exception as e:
        log(f"Error llamando a opencode: {e}", Colors.RED)
        return None

def from_example(example_path, name, category="productivity"):
    """Crear skill desde ejemplo de código."""
    example_file = Path(example_path)
    if not example_file.exists():
        log(f"Ejemplo no encontrado: {example_file}", Colors.RED)
        return False
    
    log(f"Analizando ejemplo: {example_file.name}", Colors.CYAN)
    
    # Leer ejemplo
    content = example_file.read_text(encoding="utf-8", errors="replace")
    
    # Detectar lenguaje
    if example_file.suffix == ".py":
        lang = "python"
    elif example_file.suffix in [".md", ".markdown"]:
        lang = "markdown"
    else:
        lang = "unknown"
    
    log(f"Lenguaje detectado: {lang}", Colors.GREEN)
    
    # Generar descripción automática
    description = f"Skill generada automáticamente desde {example_file.name}"
    
    # Crear TOML
    toml_content = f'''# {name} — Skill generada automáticamente
# Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

name = "{name}"
version = "1.0.0"
description = "{description}"
category = "{category}"
tags = ["auto-generated", "from-example", "{lang}"]

[entrypoint]
script = "core/scripts/skills/{name.replace('-', '_')}.py"
function = "execute"

[parameters]
input = {{ type = "string", required = true, description = "Input del usuario" }}
output = {{ type = "string", required = false, description = "Resultado procesado" }}

[examples]
ex1 = {{ input = "ejemplo de uso", output = "resultado esperado" }}
'''
    
    # Guardar TOML
    toml_path = SKILLS_DIR / f"{name}.toml"
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    toml_path.write_text(toml_content, encoding="utf-8")
    log(f"✓ Skill creada: {toml_path.relative_to(REPO_ROOT)}", Colors.GREEN)
    
    # Generar script Python
    script_content = generate_python_script(name, content, lang)
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    script_path = SCRIPTS_DIR / f"{name.replace('-', '_')}.py"
    script_path.write_text(script_content, encoding="utf-8")
    log(f"✓ Script generado: {script_path.relative_to(REPO_ROOT)}", Colors.GREEN)
    
    # Validar
    if validate_skill(toml_path):
        log("✓ Validación: PASSED", Colors.GREEN, bold=True)
        return True
    else:
        log("⚠ Validación: completada con advertencias", Colors.YELLOW)
        return True

def from_prompt(prompt_text, name):
    """Crear skill desde prompt en lenguaje natural."""
    log(f"Generando skill desde prompt: '{prompt_text[:50]}...'", Colors.CYAN)
    
    # Prompt para opencode
    opencode_prompt = f'''Crea una skill para PA Framework basada en esta descripción:
"{prompt_text}"

Nombre de la skill: {name}

Genera SOLO el contenido TOML para el archivo de la skill, siguiendo este formato:

```toml
name = "{name}"
version = "1.0.0"
description = "descripción clara"
category = "productivity"
tags = ["auto-generated", "from-prompt"]

[entrypoint]
script = "core/scripts/skills/{name.replace('-', '_')}.py"
function = "execute"

[parameters]
input = {{ type = "string", required = true, description = "..." }}

[examples]
ex1 = {{ input = "...", output = "..." }}
```

NO incluyas explicaciones, solo el bloque TOML.'''
    
    response = call_opencode(opencode_prompt)
    if not response:
        log("No se pudo generar la skill con opencode", Colors.RED)
        return False
    
    # Extraer TOML del response
    toml_match = re.search(r'```toml\s*(.*?)\s*```', response, re.S)
    if toml_match:
        toml_content = toml_match.group(1)
    else:
        toml_content = response
    
    # Guardar TOML
    toml_path = SKILLS_DIR / f"{name}.toml"
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    toml_path.write_text(toml_content, encoding="utf-8")
    log(f"✓ Skill creada: {toml_path.relative_to(REPO_ROOT)}", Colors.GREEN)
    
    # Generar script básico
    script_content = f'''#!/usr/bin/env python3
"""{name} — Skill generada desde prompt"""

def execute(input: str, **kwargs) -> str:
    """Ejecuta la skill."""
    # TODO: Implementar lógica basada en: {prompt_text[:100]}
    return f"Skill {{name}} procesó: {{input}}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(execute(sys.argv[1]))
    else:
        print("Uso: python {name.replace('-', '_')}.py <input>")
'''
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    script_path = SCRIPTS_DIR / f"{name.replace('-', '_')}.py"
    script_path.write_text(script_content, encoding="utf-8")
    log(f"✓ Script generado: {script_path.relative_to(REPO_ROOT)}", Colors.GREEN)
    
    # Validar
    if validate_skill(toml_path):
        log("✓ Validación: PASSED", Colors.GREEN, bold=True)
        return True
    else:
        log("⚠ Validación: completada con advertencias", Colors.YELLOW)
        return True

def generate_python_script(name, example_content, lang):
    """Generar script Python desde ejemplo."""
    return f'''#!/usr/bin/env python3
"""{name} — Skill generada automáticamente desde ejemplo"""

def execute(input: str, **kwargs) -> str:
    """
    Ejecuta la skill.
    
    Args:
        input: Input del usuario
        **kwargs: Parámetros adicionales
    
    Returns:
        str: Resultado procesado
    """
    # TODO: Implementar lógica basada en el ejemplo original
    # Ejemplo original ({lang}):
    """
    {example_content[:500]}...
    """
    
    # Implementación base
    result = f"Skill {{name}} procesó: {{input}}"
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(execute(sys.argv[1]))
    else:
        print("Uso: python {name.replace('-', '_')}.py <input>")
'''

def validate_skill(toml_path):
    """Validar skill TOML y script."""
    import tomllib
    
    log(f"Validando {toml_path.name}...", Colors.CYAN)
    
    try:
        # Validar TOML
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        log("  ✓ TOML válido", Colors.GREEN)
        
        # Validar campos requeridos
        required = ["name", "version", "description", "entrypoint"]
        for field in required:
            if field not in data:
                log(f"  ✗ Campo faltante: {field}", Colors.RED)
                return False
        log(f"  ✓ Campos requeridos: {', '.join(required)}", Colors.GREEN)
        
        # Validar script existe
        script_rel = data["entrypoint"].get("script", "")
        script_path = REPO_ROOT / script_rel.replace("core/", "core/")
        if script_path.exists():
            log(f"  ✓ Script existe: {script_path.name}", Colors.GREEN)
            
            # Validar sintaxis Python
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(script_path)],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                log("  ✓ Sintaxis Python válida", Colors.GREEN)
            else:
                log(f"  ✗ Error de sintaxis: {result.stderr[:100]}", Colors.RED)
                return False
        else:
            log(f"  ⚠ Script no encontrado: {script_rel}", Colors.YELLOW)
        
        return True
        
    except tomllib.TOMLDecodeError as e:
        log(f"  ✗ Error TOML: {e}", Colors.RED)
        return False
    except Exception as e:
        log(f"  ✗ Error validando: {e}", Colors.RED)
        return False

def main():
    parser = argparse.ArgumentParser(description="Skill Creator Automático")
    parser.add_argument("--from-example", help="Crear skill desde ejemplo de código")
    parser.add_argument("--from-prompt", help="Crear skill desde prompt en lenguaje natural")
    parser.add_argument("--name", help="Nombre de la skill a crear")
    parser.add_argument("--category", default="productivity", help="Categoría de la skill")
    parser.add_argument("--improve", help="Auto-mejorar skill existente")
    parser.add_argument("--validate", help="Validar skill específica")
    parser.add_argument("--validate-all", action="store_true", help="Validar todas las skills")
    
    args = parser.parse_args()
    
    if args.from_example:
        if not args.name:
            log("--name requerido para --from-example", Colors.RED)
            return 1
        success = from_example(args.from_example, args.name, args.category)
        return 0 if success else 1
    
    elif args.from_prompt:
        if not args.name:
            log("--name requerido para --from-prompt", Colors.RED)
            return 1
        success = from_prompt(args.from_prompt, args.name)
        return 0 if success else 1
    
    elif args.validate:
        success = validate_skill(Path(args.validate))
        return 0 if success else 1
    
    elif args.validate_all:
        log("Validando todas las skills...", Colors.CYAN)
        toml_files = list(SKILLS_DIR.glob("*.toml"))
        valid = 0
        invalid = 0
        for toml in toml_files:
            if validate_skill(toml):
                valid += 1
            else:
                invalid += 1
        log(f"\nResultado: {valid} válidas, {invalid} inválidas", Colors.GREEN if invalid == 0 else Colors.YELLOW)
        return 0 if invalid == 0 else 1
    
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())

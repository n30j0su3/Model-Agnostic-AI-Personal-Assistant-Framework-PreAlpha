#!/usr/bin/env python3
"""
Script Fixer - Corrige automáticamente problemas cross-platform en scripts Python.

Uso:
    python fix_script.py <archivo.py> [--output <archivo_salida>]

Ejemplos:
    python fix_script.py mi_script.py --output mi_script_fixed.py
    python fix_script.py mi_script.py --in-place
    python fix_script.py . --recursive --in-place

Precaución: Siempre revisar los cambios antes de commit.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple


class ScriptFixer:
    """Corrige automáticamente problemas cross-platform."""

    # Mapeo de emojis a ASCII
    EMOJI_REPLACEMENTS = {
        "✅": "[OK]",
        "✓": "[OK]",
        "☑": "[OK]",
        "❌": "[ERROR]",
        "✗": "[ERROR]",
        "✘": "[ERROR]",
        "⚠️": "[WARN]",
        "⚠": "[WARN]",
        "❗": "[WARN]",
        "❕": "[INFO]",
        "ℹ️": "[INFO]",
        "ℹ": "[INFO]",
        "➜": "->",
        "→": "->",
        "•": "-",
        "·": "-",
        "●": "-",
        "▸": ">",
        "►": ">",
        "◆": "*",
        "★": "*",
        "☆": "*",
        "🚀": "[START]",
        "📦": "[PKG]",
        "🔍": "[SEARCH]",
        "📝": "[EDIT]",
        "💡": "[TIP]",
        "🎯": "[GOAL]",
        "🔧": "[FIX]",
        "📊": "[STATS]",
        "🏢": "[ORG]",
        "👋": "[HI]",
        "🎨": "[ART]",
        "📚": "[DOC]",
        "🔖": "[BOOKMARK]",
        "🏷️": "[TAG]",
        "📌": "[PIN]",
        "🔗": "[LINK]",
        "📎": "[ATTACH]",
        "✂️": "[CUT]",
        "📋": "[CLIPBOARD]",
        "📁": "[FOLDER]",
        "📂": "[OPEN_FOLDER]",
        "🗂️": "[INDEX]",
        "🗄️": "[ARCHIVE]",
        "🗑️": "[TRASH]",
        "📧": "[EMAIL]",
        "📨": "[INCOMING]",
        "📩": "[DOWNLOAD]",
        "📤": "[UPLOAD]",
        "📥": "[INBOX]",
        "📦": "[PACKAGE]",
        "📫": "[MAILBOX]",
        "📪": "[CLOSED_MAILBOX]",
        "📬": "[OPEN_MAILBOX]",
        "📭": "[NO_MAIL]",
        "📮": "[POSTBOX]",
        "🗳️": "[BALLOT]",
        "✏️": "[EDIT]",
        "✒️": "[PEN]",
        "🖋️": "[FOUNTAIN_PEN]",
        "🖊️": "[BALLPOINT]",
        "🖌️": "[PAINTBRUSH]",
        "🖍️": "[CRAYON]",
        "📝": "[MEMO]",
        "💼": "[BRIEFCASE]",
        "📁": "[FILE_FOLDER]",
        "📂": "[OPEN_FILE_FOLDER]",
        "🗂️": "[CARD_INDEX]",
        "📅": "[CALENDAR]",
        "📆": "[TEAR_OFF_CALENDAR]",
        "🗒️": "[SPIRAL_NOTEPAD]",
        "🗓️": "[SPIRAL_CALENDAR]",
        "📇": "[CARD_INDEX]",
        "📈": "[CHART_INCREASING]",
        "📉": "[CHART_DECREASING]",
        "📊": "[BAR_CHART]",
        "📋": "[CLIPBOARD]",
        "📌": "[PUSHPIN]",
        "📍": "[ROUND_PUSHPIN]",
        "📎": "[PAPERCLIP]",
        "🖇️": "[LINKED_PAPERCLIPS]",
        "📏": "[STRAIGHT_RULER]",
        "📐": "[TRIANGULAR_RULER]",
        "✂️": "[SCISSORS]",
        "🗃️": "[CARD_FILE_BOX]",
        "🗄️": "[FILE_CABINET]",
        "🗑️": "[WASTEBASKET]",
        "🔒": "[LOCK]",
        "🔓": "[UNLOCK]",
        "🔏": "[LOCK_WITH_INK]",
        "🔐": "[CLOSED_LOCK]",
        "🔑": "[KEY]",
        "🗝️": "[OLD_KEY]",
        "🔨": "[HAMMER]",
        "🪓": "[AXE]",
        "⛏️": "[PICK]",
        "⚒️": "[HAMMER_PICK]",
        "🛠️": "[HAMMER_WRENCH]",
        "🗡️": "[DAGGER]",
        "⚔️": "[CROSSED_SWORDS]",
        "🔫": "[PISTOL]",
        "🏹": "[BOW_ARROW]",
        "🛡️": "[SHIELD]",
        "🔧": "[WRENCH]",
        "🔩": "[NUT_BOLT]",
        "⚙️": "[GEAR]",
        "🗜️": "[CLAMP]",
        "⚖️": "[BALANCE_SCALE]",
        "🦯": "[PROBING_CANE]",
        "🔗": "[LINK]",
        "⛓️": "[CHAINS]",
        "🧰": "[TOOLBOX]",
        "🧲": "[MAGNET]",
        "🧪": "[TEST_TUBE]",
        "🧫": "[PETRI_DISH]",
        "🧬": "[DNA]",
        "🔬": "[MICROSCOPE]",
        "🔭": "[TELESCOPE]",
        "📡": "[SATELLITE_ANTENNA]",
        "💉": "[SYRINGE]",
        "🩸": "[DROP_OF_BLOOD]",
        "💊": "[PILL]",
        "🩹": "[ADHESIVE_BANDAGE]",
        "🩺": "[STETHOSCOPE]",
        "🌡️": "[THERMOMETER]",
        "🧹": "[BROOM]",
        "🧺": "[BASKET]",
        "🧻": "[ROLL_OF_PAPER]",
        "🚽": "[TOILET]",
        "🚰": "[POTABLE_WATER]",
        "🚿": "[SHOWER]",
        "🛁": "[BATHTUB]",
        "🛀": "[PERSON_TAKING_BATH]",
        "🧼": "[SOAP]",
        "🧽": "[SPONGE]",
        "🧴": "[LOTION_BOTTLE]",
        "🛎️": "[BELLHOP_BELL]",
        "🔑": "[KEY]",
        "🗝️": "[OLD_KEY]",
    }

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content: str = ""
        self.lines: List[str] = []
        self.changes: List[Tuple[int, str, str]] = []

        # Leer archivo
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.content = f.read()
                self.lines = self.content.split("\n")
        except Exception as e:
            raise Exception(f"Error leyendo archivo: {e}")

    def fix_all(self) -> str:
        """Aplica todas las correcciones y retorna el contenido fijado."""
        content = self.content

        # Aplicar fixes en orden
        content = self._fix_emojis(content)
        content = self._fix_open_encoding(content)
        content = self._fix_shebang(content)

        return content

    def _fix_emojis(self, content: str) -> str:
        """Reemplaza emojis con equivalentes ASCII."""
        for emoji, replacement in self.EMOJI_REPLACEMENTS.items():
            if emoji in content:
                content = content.replace(emoji, replacement)
                # Registrar cambio
                for i, line in enumerate(self.lines, 1):
                    if emoji in line:
                        self.changes.append((i, emoji, replacement))

        return content

    def _fix_open_encoding(self, content: str) -> str:
        """Agrega encoding='utf-8' a open() que no lo tienen."""
        # Patrón para open() sin encoding
        # Busca: open(r'...') o open("...") sin encoding
        pattern = r"open\s*\(\s*([^,]+)\s*\)"

        def replacer(match):
            args = match.group(1).strip()
            # Si ya tiene modo (ej: 'r', 'w'), agregar encoding después
            if args.endswith(
                (
                    "'r'",
                    '"r"',
                    "'w'",
                    '"w"',
                    "'a'",
                    '"a"',
                    "'rb'",
                    '"rb"',
                    "'wb'",
                    '"wb"',
                )
            ):
                return f"open({args}, encoding='utf-8')"
            else:
                # Sin modo, agregar modo='r' explícito y encoding
                return f"open({args}, 'r', encoding='utf-8')"

        # Solo aplicar a líneas que no tienen ya encoding
        lines = content.split("\n")
        new_lines = []

        for i, line in enumerate(lines):
            if "open(" in line and "encoding" not in line:
                # Verificar que no sea un comentario
                stripped = line.strip()
                if not stripped.startswith("#"):
                    # Aplicar regex
                    new_line = re.sub(pattern, replacer, line)
                    if new_line != line:
                        self.changes.append((i + 1, line, new_line))
                        line = new_line

            new_lines.append(line)

        return "\n".join(new_lines)

    def _fix_shebang(self, content: str) -> str:
        """Asegura shebang correcto si es un script ejecutable."""
        lines = content.split("\n")

        # Verificar si ya tiene shebang
        if lines and lines[0].startswith("#!"):
            shebang = lines[0]
            # Corregir si es necesario
            if "python" in shebang.lower() and "env" not in shebang:
                new_shebang = "#!/usr/bin/env python3"
                lines[0] = new_shebang
                self.changes.append((1, shebang, new_shebang))
                return "\n".join(lines)
        elif not Path(self.file_path).name == "__init__.py":
            # Agregar shebang si no lo tiene y no es __init__.py
            new_shebang = "#!/usr/bin/env python3\n"
            content = new_shebang + content
            self.changes.append((1, "", new_shebang.strip()))

        return content

    def get_changes_summary(self) -> str:
        """Genera resumen de cambios realizados."""
        if not self.changes:
            return "No se realizaron cambios."

        summary = [f"\nCambios realizados ({len(self.changes)}):"]
        summary.append("-" * 60)

        for line_num, original, replacement in self.changes[:20]:  # Limitar a 20
            summary.append(f"  Línea {line_num}:")
            summary.append(
                f"    - {original[:60]}{'...' if len(original) > 60 else ''}"
            )
            summary.append(
                f"    + {replacement[:60]}{'...' if len(replacement) > 60 else ''}"
            )

        if len(self.changes) > 20:
            summary.append(f"  ... y {len(self.changes) - 20} cambios más")

        return "\n".join(summary)

    def save(self, output_path: str = None, in_place: bool = False) -> None:
        """Guarda el archivo fijado."""
        fixed_content = self.fix_all()

        if in_place:
            output_path = str(self.file_path)
            # Backup
            backup_path = str(self.file_path) + ".backup"
            shutil.copy2(str(self.file_path), backup_path)
            print(f"[BACKUP] Creado: {backup_path}")

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            print(f"[SAVED] Archivo guardado: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Corrige automáticamente problemas cross-platform en scripts Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Crear copia corregida
  python fix_script.py mi_script.py --output mi_script_fixed.py
  
  # Corregir en lugar (crea backup)
  python fix_script.py mi_script.py --in-place
  
  # Procesar directorio completo
  python fix_script.py . --recursive --in-place
        """,
    )

    parser.add_argument("path", help="Archivo o directorio a procesar")
    parser.add_argument("--output", "-o", help="Archivo de salida")
    parser.add_argument(
        "--in-place",
        "-i",
        action="store_true",
        help="Modificar archivo en lugar (crea backup)",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Procesar recursivamente directorios",
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Mostrar cambios sin aplicarlos"
    )

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        # Procesar archivo individual
        print(f"\n{'=' * 60}")
        print(f"Procesando: {path}")
        print("=" * 60)

        try:
            fixer = ScriptFixer(str(path))
            fixed_content = fixer.fix_all()

            print(fixer.get_changes_summary())

            if args.dry_run:
                print("\n[DRY-RUN] No se guardaron cambios")
            else:
                fixer.save(args.output, args.in_place)
                print("\n[OK] Procesamiento completado")

        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)

    elif path.is_dir():
        # Procesar directorio
        if args.recursive:
            files = list(path.rglob("*.py"))
        else:
            files = list(path.glob("*.py"))

        if not files:
            print(f"[WARN] No se encontraron archivos Python en {path}")
            sys.exit(0)

        print(f"\nProcesando {len(files)} archivos...")

        for file in sorted(files):
            print(f"\n  {file}")
            try:
                fixer = ScriptFixer(str(file))
                fixed_content = fixer.fix_all()

                if fixer.changes:
                    print(f"    {len(fixer.changes)} cambios")
                    if not args.dry_run:
                        if args.in_place:
                            fixer.save(in_place=True)
                        # Si no es in-place y no hay output específico, no guardar
                else:
                    print(f"    Sin cambios necesarios")

            except Exception as e:
                print(f"    [ERROR] {e}")

        print(f"\n{'=' * 60}")
        print(f"Procesados {len(files)} archivos")
        print("=" * 60)

    else:
        print(f"[ERROR] No se encontró: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()

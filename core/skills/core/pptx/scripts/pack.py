#!/usr/bin/env python3
import os
import sys
import zipfile
from pathlib import Path


def pack(input_dir, output_file):
    """Packs a directory back into an Office file (zip)."""
    input_dir = Path(input_dir).resolve()
    output_file = Path(output_file).resolve()

    if not input_dir.exists():
        print(f"Error: {input_dir} not found.")
        return False

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(input_dir)
                zip_ref.write(file_path, arcname)

    print(f"[OK] Packed {input_dir} into {output_file.name}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pack.py <input_dir> <output.docx/pptx/xlsx>")
    else:
        pack(sys.argv[1], sys.argv[2])

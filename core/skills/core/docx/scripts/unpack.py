#!/usr/bin/env python3
import os
import sys
import zipfile
import shutil
from pathlib import Path

def unpack(office_file, output_dir):
    """Unpacks an Office file (zip) to a directory."""
    office_file = Path(office_file).resolve()
    output_dir = Path(output_dir).resolve()
    
    if not office_file.exists():
        print(f"Error: {office_file} not found.")
        return False
    
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    with zipfile.ZipFile(office_file, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    
    print(f"✓ Unpacked {office_file.name} to {output_dir}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python unpack.py <file.docx/pptx/xlsx> <output_dir>")
    else:
        unpack(sys.argv[1], sys.argv[2])

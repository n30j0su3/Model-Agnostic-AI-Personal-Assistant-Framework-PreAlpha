#!/usr/bin/env python3
"""
recalc.py - Recalculates Excel formulas using LibreOffice headless mode.
This is a standard utility for AgentSkills xlsx.
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

def find_libreoffice():
    """Locates LibreOffice executable based on platform."""
    if sys.platform == "win32":
        paths = [
            Path("C:/Program Files/LibreOffice/program/soffice.exe"),
            Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
        ]
        for p in paths:
            if p.exists():
                return str(p)
    elif sys.platform == "darwin":
        p = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        if p.exists():
            return str(p)
    else: # Linux
        return shutil.which("soffice") or shutil.which("libreoffice")
    
    return None

def recalculate(file_path, timeout=30):
    """
    Recalculates formulas by opening and saving the file with LibreOffice.
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        return False

    soffice = find_libreoffice()
    if not soffice:
        print("Error: LibreOffice (soffice) not found. Please install it.")
        return False

    print(f"Recalculating {file_path.name} using LibreOffice...")
    
    # We use --headless and --convert-to xlsx to trigger recalculation
    # A common trick is to convert to the same format
    try:
        cmd = [
            soffice,
            "--headless",
            "--convert-to", "xlsx",
            "--outdir", str(file_path.parent),
            str(file_path)
        ]
        
        subprocess.run(cmd, check=True, timeout=timeout, capture_output=True)
        print("✓ Formulas recalculated successfully.")
        return True
    except subprocess.TimeoutExpired:
        print(f"Error: Recalculation timed out after {timeout}s.")
    except Exception as e:
        print(f"Error during recalculation: {e}")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recalc.py <file.xlsx> [timeout]")
        sys.exit(1)
    
    path = sys.argv[1]
    time_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    if recalculate(path, time_limit):
        sys.exit(0)
    else:
        sys.exit(1)

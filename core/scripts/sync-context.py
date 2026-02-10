#!/usr/bin/env python3
"""
Sync Context — Pre-Alpha
Sincroniza MASTER.md con archivos de contexto por herramienta.
"""

import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
BACKUP_DIR = CONTEXT_DIR / "backups"

LOG_DIR = REPO_ROOT / "logs" / "system"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "context-sync.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

TOOLS = ["opencode", "claude", "gemini"]
START_MARKER = "<!-- MASTER-CONTEXT-START -->"
END_MARKER = "<!-- MASTER-CONTEXT-END -->"


class ContextSynchronizer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_backup(self):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_sub = BACKUP_DIR / self.timestamp
        backup_sub.mkdir(exist_ok=True)
        count = 0
        for fname in ["MASTER.md"] + [f"{t}.md" for t in TOOLS]:
            src = CONTEXT_DIR / fname
            if src.exists():
                shutil.copy2(src, backup_sub / fname)
                count += 1
        logging.info(f"Backup: {backup_sub.name} ({count} archivos)")

    def validate_master(self, content: str) -> bool:
        required = ["# MASTER CONTEXT", "## Active Workspaces", "## Current Focus"]
        missing = [r for r in required if r not in content]
        if missing:
            logging.error(f"MASTER.md inválido. Faltan: {missing}")
            return False
        return True

    def get_master_content(self) -> str | None:
        master = CONTEXT_DIR / "MASTER.md"
        if not master.exists():
            template = CONTEXT_DIR / "MASTER.template.md"
            if template.exists():
                logging.warning("MASTER.md no existe. Restaurando desde template.")
                content = template.read_text(encoding="utf-8")
                master.write_text(content, encoding="utf-8")
                return content
            return None
        return master.read_text(encoding="utf-8")

    def sync_file(self, tool_name: str, master_content: str):
        tool_file = CONTEXT_DIR / f"{tool_name}.md"
        sync_block = f"{START_MARKER}\n{master_content}\n{END_MARKER}"
        header = f"# {tool_name.capitalize()} Context\n\n"

        if tool_file.exists():
            content = tool_file.read_text(encoding="utf-8")
            if START_MARKER in content:
                header = content.split(START_MARKER)[0]

        tool_file.write_text(f"{header}{sync_block}", encoding="utf-8")
        logging.info(f"✅ Sincronizado: {tool_name}.md")

    def update_last_sync(self):
        try:
            (REPO_ROOT / ".last_sync").touch()
        except Exception as e:
            logging.warning(f"No se pudo actualizar timestamp: {e}")

    def run(self) -> bool:
        logging.info("--- Iniciando Sync de Contexto ---")

        self.create_backup()

        content = self.get_master_content()
        if not content:
            logging.error("No se pudo leer MASTER.md")
            return False

        if not self.validate_master(content):
            return False

        for tool in TOOLS:
            try:
                self.sync_file(tool, content)
            except Exception as e:
                logging.error(f"Error en {tool}: {e}")

        self.update_last_sync()
        logging.info("--- Sync Completado ---")
        return True


if __name__ == "__main__":
    sync = ContextSynchronizer()
    success = sync.run()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
PA Framework — Session Auto-save
Sincroniza interacciones recientes con el archivo de sesión Markdown.

Uso:
    python core/scripts/session_autosave.py
    python core/scripts/session_autosave.py --summary "Breve resumen de lo hecho"
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Paths (cross-platform: use Path(__file__).parent)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CORE_DIR = REPO_ROOT / "core"
CONTEXT_DIR = CORE_DIR / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
INTERACTIONS_DIR = KNOWLEDGE_DIR / "interactions"

def get_today_session_file() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return SESSIONS_DIR / f"{today}.md"

def get_today_log_file() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return INTERACTIONS_DIR / f"interactions-{today}.log"

def extract_interactions_from_log() -> List[Dict]:
    log_file = get_today_log_file()
    if not log_file.exists():
        return []
    
    interactions = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    interactions.append(event)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    
    return interactions

def update_session_md(interactions: List[Dict], summary_update: Optional[str] = None):
    session_file = get_today_session_file()
    if not session_file.exists():
        return False
    
    content = session_file.read_text(encoding="utf-8")
    
    # 1. Identificar últimos eventos ya registrados en el MD
    # 2. Generar nuevos bullets para el Log de Actividades
    new_activities = []
    
    for event in interactions:
        timestamp = event.get("timestamp", "")
        time_short = timestamp.split("T")[1][:5] if "T" in timestamp else "--:--"
        event_type = event.get("event", "unknown")
        
        activity = ""
        if event_type == "prompt":
            activity = f"Interacción con {event.get('agent', 'AI')} ({event.get('model', 'model')})"
        elif event_type == "file_write":
            activity = f"Escritura en `{event.get('file', 'archivo')}`"
        elif event_type == "agent_call":
            activity = f"Llamada a agente `{event.get('agent', 'agente')}`: {event.get('action', 'acción')}"
        elif event_type == "skill_call":
            activity = f"Uso de skill `{event.get('skill', 'skill')}`"
        
        if activity and activity not in content:
            new_activities.append(f"- [{time_short}] {activity}")

    # 3. Insertar en Log de Actividades
    if new_activities:
        # FIX: Regex pattern handles extra newlines (Windows/macOS/Linux safe)
        pattern = r"(##\s+Log\s+de\s+Actividades\s*\n+)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            insert_point = match.end()
            content = content[:insert_point] + "\n".join(new_activities) + "\n" + content[insert_point:]
        else:
            content += "\n## Log de Actividades\n" + "\n".join(new_activities) + "\n"

    # 4. Actualizar Resumen si se proporcionó
    if summary_update:
        summary_pattern = r"(##\s+Resumen\s*\n)(.+?)(?=\n##|\Z)"
        if re.search(summary_pattern, content, re.DOTALL | re.IGNORECASE):
            content = re.sub(
                summary_pattern,
                f"\\1{summary_update}\n",
                content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            content += f"\n## Resumen\n{summary_update}\n"

    # 5. Actualizar status y last_seen (time_end) en frontmatter
    now_time = datetime.now().strftime("%H:%M")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            if "status: active" not in frontmatter and "status: completed" not in frontmatter:
                frontmatter += "\nstatus: active"
            
            if "time_end:" in frontmatter:
                frontmatter = re.sub(r"time_end:\s*.*", f"time_end: {now_time}", frontmatter)
            else:
                frontmatter += f"\ntime_end: {now_time}"
            
            content = "---" + frontmatter + "---" + parts[2]

    session_file.write_text(content, encoding="utf-8")
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="PA Framework - Session Auto-save")
    parser.add_argument("--summary", type=str, help="Actualizar resumen de la sesión")
    args = parser.parse_args()
    
    interactions = extract_interactions_from_log()
    if update_session_md(interactions, args.summary):
        print("[OK] Sesión auto-guardada correctamente.")
    else:
        print("[ERROR] No se pudo auto-guardar la sesión.")

if __name__ == "__main__":
    main()
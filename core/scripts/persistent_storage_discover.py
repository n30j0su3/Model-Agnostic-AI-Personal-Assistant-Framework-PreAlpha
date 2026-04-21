#!/usr/bin/env python3
"""
Persistent Storage Discovery — PA Framework v0.3.7-alpha
Auto-descubre SQLite, Wiki, MD al iniciar y reporta estado.

Creator: FreakingJSON (instagram.com/freakingjson, freakingjson.com)
"""

import json
import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

try:
    import yaml
except Exception:
    yaml = None


# --- RESOLVE PATHS ---
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
STANDALONE_CONFIG_DIR = Path.home() / ".pa-framework"
CONFIG_FILE = STANDALONE_CONFIG_DIR / "config.json"
FRAMEWORK_CONFIG_FILE = REPO_ROOT / "config" / "framework.yaml"

# Storage locations
DEFAULT_STORAGE_LOCATIONS = {
    "sqlite": {
        "path": REPO_ROOT / "data" / "sessions.db",
        "description": "Session persistence SQLite",
        "type": "sqlite"
    },
    "wiki": {
        "path": CONTEXT_DIR / "knowledge" / "wiki",
        "description": "Wiki knowledge store",
        "type": "wiki"
    },
    "md_memory": {
        "path": CONTEXT_DIR / "memory",
        "description": "Markdown memory files",
        "type": "md"
    },
    "sessions_md": {
        "path": CONTEXT_DIR / "sessions",
        "description": "Session Markdown logs",
        "type": "md"
    }
}


# --- STORAGE CHECKERS ---
def check_sqlite(db_path: Path) -> dict:
    """Check SQLite database status."""
    result = {
        "available": False,
        "exists": db_path.exists(),
        "tables": [],
        "size_kb": 0,
        "last_modified": None
    }
    
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            result["tables"] = [row[0] for row in cursor.fetchall()]
            conn.close()
            result["available"] = True
            result["empty"] = len(result["tables"]) == 0
            result["size_kb"] = db_path.stat().st_size // 1024
            result["last_modified"] = datetime.fromtimestamp(db_path.stat().st_mtime).isoformat()
        except Exception as e:
            result["error"] = str(e)
    
    return result


def check_wiki(wiki_path: Path) -> dict:
    """Check wiki storage status (local persistence first, MkDocs optional)."""
    result = {
        "available": False,
        "exists": wiki_path.exists(),
        "docs_count": 0,
        "mkdocs_yml": False,
        "mkdocs_docs_count": 0,
        "last_modified": None
    }
    
    if wiki_path.exists():
        try:
            # 1) Local relational wiki store (core/.context/knowledge/wiki)
            local_md = list(wiki_path.glob("**/*.md"))
            result["docs_count"] = len(local_md)

            # 2) Optional MkDocs project at repo root (docs/ + mkdocs.yml)
            mkdocs_yml = REPO_ROOT / "mkdocs.yml"
            result["mkdocs_yml"] = mkdocs_yml.exists()
            if result["mkdocs_yml"]:
                mkdocs_docs = REPO_ROOT / "docs"
                if mkdocs_docs.exists():
                    result["mkdocs_docs_count"] = len(list(mkdocs_docs.glob("**/*.md")))

            # Layer availability = storage exists; docs_count indicates populated state.
            result["available"] = True
            result["empty"] = result["docs_count"] == 0
            
            # Get most recent file modification
            recent_files = sorted(wiki_path.glob("**/*"), key=lambda f: f.stat().st_mtime, reverse=True)
            if recent_files:
                result["last_modified"] = datetime.fromtimestamp(recent_files[0].stat().st_mtime).isoformat()
        except Exception as e:
            result["error"] = str(e)
    
    return result


def check_md_memory(md_path: Path) -> dict:
    """Check Markdown memory directory status."""
    result = {
        "available": False,
        "exists": md_path.exists(),
        "files_count": 0,
        "files": [],
        "last_modified": None
    }
    
    if md_path.exists():
        try:
            md_files = list(md_path.glob("**/*.md"))
            result["files_count"] = len(md_files)
            result["files"] = [f.name for f in md_files[:10]]  # First 10
            
            # Layer is available if directory exists; files_count indicates populated state.
            result["available"] = True
            result["empty"] = result["files_count"] == 0
            
            recent_files = sorted(md_files, key=lambda f: f.stat().st_mtime, reverse=True)
            if recent_files:
                result["last_modified"] = datetime.fromtimestamp(recent_files[0].stat().st_mtime).isoformat()
        except Exception as e:
            result["error"] = str(e)
    
    return result


def discover_all_storage(custom_paths: dict = None) -> dict:
    """Discover all persistent storage systems."""
    locations = DEFAULT_STORAGE_LOCATIONS.copy()
    
    # Override with custom paths from config
    if custom_paths:
        if "sqlite_path" in custom_paths and custom_paths["sqlite_path"]:
            locations["sqlite"]["path"] = Path(custom_paths["sqlite_path"])
        if "wiki_path" in custom_paths and custom_paths["wiki_path"]:
            locations["wiki"]["path"] = Path(custom_paths["wiki_path"])
        if "memory_path" in custom_paths and custom_paths["memory_path"]:
            locations["md_memory"]["path"] = Path(custom_paths["memory_path"])
        if "sessions_path" in custom_paths and custom_paths["sessions_path"]:
            locations["sessions_md"]["path"] = Path(custom_paths["sessions_path"])
    
    results = {}
    
    for name, config in locations.items():
        path = config["path"]
        storage_type = config["type"]
        
        if storage_type == "sqlite":
            results[name] = check_sqlite(path)
        elif storage_type == "wiki":
            results[name] = check_wiki(path)
        elif storage_type == "md":
            results[name] = check_md_memory(path)
        
        results[name]["path"] = str(path)
        results[name]["description"] = config["description"]
        results[name]["type"] = storage_type
    
    return results


def load_config() -> dict:
    """Load paths from framework.yaml first, then optional standalone overrides."""
    cfg = {}

    # Primary source of truth: framework.yaml
    if FRAMEWORK_CONFIG_FILE.exists() and yaml is not None:
        try:
            with open(FRAMEWORK_CONFIG_FILE, "r", encoding="utf-8") as f:
                framework_cfg = yaml.safe_load(f) or {}
            mp = framework_cfg.get("memory_pipeline", {})
            if isinstance(mp, dict):
                paths = mp.get("paths", {})
                if isinstance(paths, dict):
                    if paths.get("sqlite"):
                        cfg["sqlite_path"] = paths["sqlite"]
                    if paths.get("wiki"):
                        cfg["wiki_path"] = paths["wiki"]
                    if paths.get("memory_md"):
                        cfg["memory_path"] = paths["memory_md"]
                    if paths.get("sessions_md"):
                        cfg["sessions_path"] = paths["sessions_md"]
        except Exception:
            pass

    # Optional legacy override (only when explicitly enabled)
    if os.environ.get("PA_FRAMEWORK_USE_STANDALONE_PATHS") == "1" and CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                standalone = json.load(f)
            if standalone.get("wiki_path"):
                cfg["wiki_path"] = standalone["wiki_path"]
            if standalone.get("memory_path"):
                cfg["memory_path"] = standalone["memory_path"]
            if standalone.get("sqlite_path"):
                cfg["sqlite_path"] = standalone["sqlite_path"]
            if standalone.get("sessions_path"):
                cfg["sessions_path"] = standalone["sessions_path"]
        except Exception:
            pass

    return cfg


def print_discovery_report(results: dict, verbose: bool = False):
    """Print human-readable discovery report."""
    print("\n" + "=" * 60)
    print("  PERSISTENT STORAGE DISCOVERY REPORT")
    print("=" * 60)
    
    available_count = sum(1 for r in results.values() if r.get("available"))
    total_count = len(results)
    
    print(f"\n  Available: {available_count}/{total_count} systems\n")
    
    for name, data in results.items():
        # ASCII-safe status icons for Windows cp1252 compatibility
        status_icon = "[OK]" if data.get("available") else "[--]"
        print(f"  {status_icon} [{name}] {data.get('description', '')}")
        print(f"      Path: {data.get('path', 'N/A')}")
        
        if data.get("available"):
            if data.get("type") == "sqlite":
                print(f"      Tables: {', '.join(data.get('tables', []))}")
                print(f"      Size: {data.get('size_kb', 0)} KB")
            elif data.get("type") == "wiki":
                print(f"      Docs: {data.get('docs_count', 0)} files")
                print(f"      mkdocs.yml: {data.get('mkdocs_yml', False)}")
            elif data.get("type") == "md":
                print(f"      Files: {data.get('files_count', 0)}")
        
        if verbose and data.get("last_modified"):
            print(f"      Last modified: {data.get('last_modified')}")
        
        if data.get("error"):
            print(f"      Error: {data.get('error')}")
        
        print()
    
    print("=" * 60)
    print(f"  Generated: {datetime.now().isoformat()}")
    print("=" * 60 + "\n")


def get_integration_status(results: dict) -> dict:
    """Return integration status for agent prompts."""
    return {
        "sqlite_available": results.get("sqlite", {}).get("available", False),
        "wiki_available": results.get("wiki", {}).get("available", False),
        "md_memory_available": results.get("md_memory", {}).get("available", False),
        "sessions_md_available": results.get("sessions_md", {}).get("available", False),
        "all_available": all(r.get("available") for r in results.values()),
        "sqlite_tables": results.get("sqlite", {}).get("tables", []),
        "wiki_docs_count": results.get("wiki", {}).get("docs_count", 0),
        "md_files_count": results.get("md_memory", {}).get("files_count", 0)
    }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PA Framework Persistent Storage Discovery"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed info")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--integration", action="store_true", help="Output integration status only")
    
    args = parser.parse_args()
    
    config = load_config()
    results = discover_all_storage(config)
    
    if args.integration:
        integration = get_integration_status(results)
        print(json.dumps(integration, indent=2))
    elif args.json:
        print(json.dumps(results, indent=2))
    else:
        print_discovery_report(results, verbose=args.verbose)
    
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
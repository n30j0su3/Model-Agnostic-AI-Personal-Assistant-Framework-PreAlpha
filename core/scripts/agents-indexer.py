#!/usr/bin/env python3
"""
Agents Indexer - PA Framework
=============================

Escanea agentes disponibles y genera/actualiza agents-index.json.
Compatible con la estructura del framework.

Uso:
    python core/scripts/agents-indexer.py           # Indexar agentes
    python core/scripts/agents-indexer.py --rebuild # Reconstruir índice completo
    python core/scripts/agents-indexer.py --check   # Solo verificar

Autor: FreakingJSON-PA Framework
Versión: 1.0.0
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
AGENTS_DIR = REPO_ROOT / "core" / "agents"
SUBAGENTS_DIR = AGENTS_DIR / "subagents"
KNOWLEDGE_DIR = REPO_ROOT / "core" / ".context" / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "agents-index.json"

KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


class AgentsIndexer:
    """Indexer for agent files with YAML frontmatter extraction."""

    def __init__(self):
        self.index = self._load_existing_index()
        self.new_agents = 0
        self.updated_agents = 0

    def _load_existing_index(self) -> dict:
        """Load existing index or create new structure."""
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass

        return {
            "version": "1.0",
            "description": "Índice de agentes disponibles en el framework",
            "last_updated": datetime.now().isoformat(),
            "total_agents": 0,
            "agents": [],
            "types": {"primary": 0, "subagent": 0},
        }

    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter from agent file."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                return self._parse_yaml_frontmatter(frontmatter)
        return {}

    def _parse_yaml_frontmatter(self, yaml_text: str) -> dict:
        """Parse simple YAML frontmatter."""
        data = {}
        current_key = None
        current_list = []
        in_list = False
        in_nested = False
        nested_key = None

        for line in yaml_text.split("\n"):
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            if line.startswith("  ") and in_list and current_key:
                if stripped.startswith("- "):
                    value = stripped[2:].strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    current_list.append(value)
                continue

            if line.startswith("  ") and in_nested and nested_key:
                if ":" in stripped:
                    nkey, nvalue = stripped.split(":", 1)
                    nkey = nkey.strip()
                    nvalue = nvalue.strip().strip('"')
                    if nested_key not in data:
                        data[nested_key] = {}
                    data[nested_key][nkey] = nvalue
                continue

            if ":" in stripped:
                if in_list and current_key:
                    data[current_key] = current_list
                    current_list = []
                    in_list = False

                key, value = stripped.split(":", 1)
                key = key.strip()
                value = value.strip()

                if value:
                    if value.startswith("[") and value.endswith("]"):
                        items = value[1:-1].split(",")
                        data[key] = [
                            i.strip().strip('"').strip("'") for i in items if i.strip()
                        ]
                    elif value.startswith('"') and value.endswith('"'):
                        data[key] = value[1:-1]
                    elif value == "true":
                        data[key] = True
                    elif value == "false":
                        data[key] = False
                    else:
                        data[key] = value
                    current_key = None
                    in_list = False
                    in_nested = False
                else:
                    current_key = key
                    in_list = False
                    in_nested = False
                    next_char_idx = yaml_text.find(stripped) + len(stripped)
                    remaining = yaml_text[next_char_idx:].lstrip()
                    if remaining.startswith("-"):
                        in_list = True
                        current_list = []
                    elif remaining.startswith("  ") and ":" in remaining.split("\n")[0]:
                        in_nested = True
                        nested_key = key

        if in_list and current_key:
            data[current_key] = current_list

        return data

    def _extract_scripts(self, content: str) -> dict:
        """Extract script references from agent content."""
        scripts = {}

        patterns = [
            (r"session-start\.py", "session_start"),
            (r"session-end\.py", "session_end"),
            (r"session-indexer\.py", "session_indexer"),
            (r"pa\.py", "pa_main"),
            (r"multi_cli_coordinator\.py", "multi_cli"),
        ]

        for pattern, script_name in patterns:
            if re.search(pattern, content):
                scripts[script_name] = f"core/scripts/{pattern}"

        return scripts

    def _extract_tools(self, frontmatter: dict) -> List[str]:
        """Extract tools list from frontmatter."""
        tools = frontmatter.get("tools", {})
        if isinstance(tools, dict):
            return [k for k, v in tools.items() if v is True]
        elif isinstance(tools, list):
            return tools
        return []

    def _extract_dependencies(self, frontmatter: dict) -> List[str]:
        """Extract dependencies from frontmatter."""
        deps = frontmatter.get("dependencies", [])
        result = []
        for dep in deps:
            if isinstance(dep, str):
                result.append(dep)
        return result

    def parse_agent_file(self, file_path: Path, agent_type: str) -> Optional[dict]:
        """Parse a single agent file and return structured data."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[WARN] Error reading {file_path}: {e}")
            return None

        frontmatter = self._extract_frontmatter(content)

        if not frontmatter.get("id"):
            name_match = re.search(r"^#\s+(@?\w+)", content, re.MULTILINE)
            agent_id = (
                name_match.group(1).lower().replace("@", "").replace("-", "_")
                if name_match
                else file_path.stem
            )
        else:
            agent_id = frontmatter.get("id", file_path.stem)

        name = frontmatter.get("name", agent_id)
        if not name.startswith("@"):
            name = f"@{name}"

        description = frontmatter.get("description", "Agente del framework")

        tools = self._extract_tools(frontmatter)
        dependencies = self._extract_dependencies(frontmatter)
        scripts = self._extract_scripts(content)

        relative_path = file_path.relative_to(REPO_ROOT)
        location = str(relative_path).replace("\\", "/")

        status = "operativo"

        agent_entry = {
            "id": agent_id,
            "name": name,
            "description": description,
            "type": agent_type,
            "location": location,
            "dependencies": dependencies,
            "tools": tools,
            "status": status,
            "scripts": scripts,
        }

        if frontmatter.get("mode"):
            agent_entry["mode"] = frontmatter.get("mode")
        if frontmatter.get("version"):
            agent_entry["version"] = frontmatter.get("version")
        if frontmatter.get("category"):
            agent_entry["category"] = frontmatter.get("category")
        if frontmatter.get("tags"):
            agent_entry["tags"] = frontmatter.get("tags")

        return agent_entry

    def index_all_agents(self):
        """Index all agent files."""
        agents = []

        primary_file = AGENTS_DIR / "pa-assistant.md"
        if primary_file.exists():
            agent = self.parse_agent_file(primary_file, "primary")
            if agent:
                agents.append(agent)

        if SUBAGENTS_DIR.exists():
            for agent_file in sorted(SUBAGENTS_DIR.glob("*.md")):
                agent = self.parse_agent_file(agent_file, "subagent")
                if agent:
                    agents.append(agent)

        print(f"[INFO] Found {len(agents)} agent files")

        existing_ids = {a["id"] for a in self.index.get("agents", [])}

        for agent in agents:
            if agent["id"] in existing_ids:
                for i, existing in enumerate(self.index["agents"]):
                    if existing["id"] == agent["id"]:
                        self.index["agents"][i] = agent
                        self.updated_agents += 1
                        break
            else:
                self.index["agents"].append(agent)
                self.new_agents += 1

        self.index["agents"].sort(
            key=lambda x: (0 if x["type"] == "primary" else 1, x["id"])
        )

        self.index["total_agents"] = len(self.index["agents"])
        self.index["last_updated"] = datetime.now().isoformat()

        primary_count = sum(1 for a in self.index["agents"] if a["type"] == "primary")
        subagent_count = sum(1 for a in self.index["agents"] if a["type"] == "subagent")
        self.index["types"] = {"primary": primary_count, "subagent": subagent_count}

        self._save_index()

        print(f"[OK] Indexed {self.index['total_agents']} agents")
        print(f"   Primary: {primary_count}")
        print(f"   Subagents: {subagent_count}")
        print(f"   New: {self.new_agents}")
        print(f"   Updated: {self.updated_agents}")

    def check_agents(self) -> bool:
        """Verify all expected agents exist."""
        issues = []

        primary_file = AGENTS_DIR / "pa-assistant.md"
        if not primary_file.exists():
            issues.append(f"Missing primary agent: {primary_file}")

        if not SUBAGENTS_DIR.exists():
            issues.append(f"Missing subagents directory: {SUBAGENTS_DIR}")
        else:
            expected_subagents = ["context-scout", "session-manager", "doc-writer"]
            for subagent in expected_subagents:
                subagent_file = SUBAGENTS_DIR / f"{subagent}.md"
                if not subagent_file.exists():
                    issues.append(f"Missing subagent: {subagent}")

        if issues:
            print("[CHECK] Issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False

        print("[CHECK] All agents present and valid")
        return True

    def _save_index(self):
        """Save index to file."""
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        print(f"[OK] Index saved to {INDEX_FILE}")

    def get_stats(self) -> dict:
        """Get statistics about indexed agents."""
        return {
            "total_agents": len(self.index.get("agents", [])),
            "types": self.index.get("types", {}),
            "last_updated": self.index.get("last_updated", ""),
        }


def main():
    parser = argparse.ArgumentParser(description="Agents Indexer for PA Framework")
    parser.add_argument(
        "--rebuild", action="store_true", help="Rebuild index from scratch"
    )
    parser.add_argument("--check", action="store_true", help="Only verify agents exist")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    indexer = AgentsIndexer()

    if args.stats:
        stats = indexer.get_stats()
        print("Agents Index Statistics:")
        print(f"  Total agents: {stats['total_agents']}")
        print(f"  Types: {stats['types']}")
        print(f"  Last updated: {stats['last_updated']}")
        return

    if args.check:
        success = indexer.check_agents()
        return 0 if success else 1

    if args.rebuild:
        print("[INFO] Rebuilding index from scratch...")
        indexer.index = indexer._load_existing_index()
        indexer.index["agents"] = []

    indexer.index_all_agents()
    return 0


if __name__ == "__main__":
    exit(main())

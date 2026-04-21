#!/usr/bin/env python3
"""
Skills Indexer - PA Framework
=============================

Escanea las skills disponibles y genera/actualiza skills-index.json
para consulta rápida por el framework y Dashboard SPA.

Uso:
    python core/scripts/skills-indexer.py           # Indexar todas las skills
    python core/scripts/skills-indexer.py --rebuild # Reconstruir índice completo
    python core/scripts/skills-indexer.py --check    # Solo verificar, no escribir

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
SKILLS_DIR = REPO_ROOT / "core" / "skills" / "core"
KNOWLEDGE_DIR = REPO_ROOT / "core" / ".context" / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "skills-index.json"

KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


class SkillsIndexer:
    """Indexer for skill directories with metadata extraction."""

    def __init__(self):
        self.index = self._load_existing_index()
        self.new_skills = 0
        self.updated_skills = 0

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
            "description": "Índice de skills disponibles en el framework",
            "last_updated": datetime.now().isoformat(),
            "total_skills": 0,
            "skills": [],
            "categories": {},
        }

    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter if present."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                data = {}
                current_key = None
                in_metadata = False
                metadata_content = {}

                for line in frontmatter.split("\n"):
                    if not line.strip():
                        continue

                    if line.startswith("  ") and current_key:
                        if current_key == "metadata":
                            in_metadata = True
                            if ":" in line.strip():
                                sub_key, sub_val = line.strip().split(":", 1)
                                metadata_content[sub_key.strip()] = (
                                    sub_val.strip().strip('"')
                                )
                        continue

                    in_metadata = False
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        current_key = key

                        if key == "metadata":
                            metadata_content = {}
                            data["metadata"] = metadata_content
                        else:
                            data[key] = value.strip('"')

                if metadata_content:
                    data["metadata"] = metadata_content

                return data
        return {}

    def _extract_description(self, content: str) -> str:
        """Extract description from SKILL.md content."""
        match = re.search(r"^#\s+.+?\n\n(.+?)(?=\n##|\n```|\Z)", content, re.DOTALL)
        if match:
            desc = match.group(1).strip()
            if len(desc) > 200:
                return desc[:197] + "..."
            return desc

        lines = content.split("\n")
        for line in lines[5:]:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("---"):
                if len(line) > 200:
                    return line[:197] + "..."
                return line

        return "Sin descripción disponible"

    def _extract_tools(self, content: str) -> List[str]:
        """Extract tool/dependency mentions from content."""
        tools = []

        tool_patterns = [
            r"```python\n(?:from|import)\s+(\w+)",
            r"pip install\s+([\w\-]+)",
            r"requires?\s*:?\s*([\w\-]+)",
            r"requiere\s+(\w+)",
        ]

        for pattern in tool_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tools.extend(matches)

        common_tools = [
            "pandas",
            "numpy",
            "matplotlib",
            "seaborn",
            "plotly",
            "pypdf",
            "pdfplumber",
            "reportlab",
            "openpyxl",
            "xlrd",
            "python-docx",
            "python-pptx",
            "Pillow",
            "PIL",
            "requests",
            "beautifulsoup4",
            "selenium",
            "pytesseract",
            "jinja2",
            "pyyaml",
            "toml",
            "jsonschema",
        ]

        content_lower = content.lower()
        for tool in common_tools:
            if tool.lower() in content_lower and tool not in tools:
                tools.append(tool)

        return list(set(tools))[:10]

    def parse_skill_directory(self, skill_dir: Path) -> Optional[dict]:
        """Parse a single skill directory and return structured data."""
        skill_id = skill_dir.name
        skill_md = skill_dir / "SKILL.md"

        if not skill_dir.is_dir():
            return None

        skill_data = {
            "id": skill_id,
            "name": f"@{skill_id}",
            "description": "Sin descripción disponible",
            "category": "core",
            "location": f"core/skills/core/{skill_id}/",
            "has_scripts": (skill_dir / "scripts").is_dir(),
            "dependencies": [],
            "tools": [],
        }

        if skill_md.exists():
            try:
                with open(skill_md, "r", encoding="utf-8") as f:
                    content = f.read()

                frontmatter = self._extract_frontmatter(content)

                if "name" in frontmatter:
                    skill_data["id"] = frontmatter["name"]
                    skill_data["name"] = f"@{frontmatter['name']}"

                if "description" in frontmatter:
                    skill_data["description"] = frontmatter["description"]

                if "dependencies" in frontmatter:
                    deps = frontmatter["dependencies"]
                    if isinstance(deps, list):
                        skill_data["dependencies"] = deps
                    elif isinstance(deps, str):
                        skill_data["dependencies"] = [
                            d.strip() for d in deps.split(",")
                        ]

                skill_data["tools"] = self._extract_tools(content)

                if not frontmatter.get("description"):
                    skill_data["description"] = self._extract_description(content)

            except Exception as e:
                print(f"[WARN] Error reading {skill_md}: {e}")

        scripts_dir = skill_dir / "scripts"
        if scripts_dir.is_dir():
            script_files = list(scripts_dir.glob("*.py"))
            if script_files:
                skill_data["scripts_count"] = len(script_files)
                skill_data["main_script"] = script_files[0].name

        return skill_data

    def index_all_skills(self):
        """Index all skill directories."""
        if not SKILLS_DIR.exists():
            print(f"[ERROR] Skills directory not found: {SKILLS_DIR}")
            return

        skill_dirs = sorted([d for d in SKILLS_DIR.iterdir() if d.is_dir()])

        print(f"[INFO] Found {len(skill_dirs)} skill directories")

        existing_ids = {s["id"] for s in self.index["skills"]}

        for skill_dir in skill_dirs:
            skill = self.parse_skill_directory(skill_dir)
            if not skill:
                continue

            if skill["id"] in existing_ids:
                for i, existing in enumerate(self.index["skills"]):
                    if existing["id"] == skill["id"]:
                        self.index["skills"][i] = skill
                        self.updated_skills += 1
                        break
            else:
                self.index["skills"].append(skill)
                self.new_skills += 1

        self.index["skills"].sort(key=lambda x: x["id"])

        self.index["total_skills"] = len(self.index["skills"])
        self.index["last_updated"] = datetime.now().isoformat()

        self._update_categories()

        self._save_index()

        print(f"[OK] Indexed {self.index['total_skills']} skills")
        print(f"   New: {self.new_skills}")
        print(f"   Updated: {self.updated_skills}")

    def _update_categories(self):
        """Update category counts."""
        categories = {}
        for skill in self.index["skills"]:
            category = skill.get("category", "core")
            categories[category] = categories.get(category, 0) + 1

        self.index["categories"] = categories

    def _save_index(self):
        """Save index to file."""
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        print(f"[OK] Index saved to {INDEX_FILE}")

    def check_only(self) -> bool:
        """Check skills without writing index."""
        if not SKILLS_DIR.exists():
            print(f"[ERROR] Skills directory not found: {SKILLS_DIR}")
            return False

        skill_dirs = sorted([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
        issues = []

        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                issues.append(f"{skill_dir.name}: Missing SKILL.md")

        print(f"[INFO] Checked {len(skill_dirs)} skills")
        if issues:
            print(f"[WARN] Found {len(issues)} issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False

        print("[OK] All skills have SKILL.md")
        return True

    def get_stats(self) -> dict:
        """Get statistics about indexed skills."""
        skills_with_scripts = sum(
            1 for s in self.index["skills"] if s.get("has_scripts")
        )
        total_tools = sum(len(s.get("tools", [])) for s in self.index["skills"])

        return {
            "total_skills": len(self.index["skills"]),
            "categories": dict(self.index.get("categories", {})),
            "skills_with_scripts": skills_with_scripts,
            "total_tools_mentioned": total_tools,
            "last_updated": self.index["last_updated"],
        }


def main():
    parser = argparse.ArgumentParser(description="Skills Indexer for PA Framework")
    parser.add_argument(
        "--rebuild", action="store_true", help="Rebuild index from scratch"
    )
    parser.add_argument(
        "--check", action="store_true", help="Only verify, don't write index"
    )
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    indexer = SkillsIndexer()

    if args.stats:
        stats = indexer.get_stats()
        print("Skills Index Statistics:")
        print(f"  Total skills: {stats['total_skills']}")
        print(f"  Categories: {stats['categories']}")
        print(f"  Skills with scripts: {stats['skills_with_scripts']}")
        print(f"  Total tools mentioned: {stats['total_tools_mentioned']}")
        print(f"  Last updated: {stats['last_updated']}")
        return

    if args.check:
        indexer.check_only()
        return

    if args.rebuild:
        print("[INFO] Rebuilding index from scratch...")
        indexer.index["skills"] = []

    indexer.index_all_skills()


if __name__ == "__main__":
    main()

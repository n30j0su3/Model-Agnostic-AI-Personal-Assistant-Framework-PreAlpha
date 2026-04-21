#!/usr/bin/env python3
"""
Project Register - Register and track projects in PA Framework memory

This solves the "Proyecto Alfa" problem - projects weren't being registered.
Now every project is tracked in SQLite + Wiki + Registry.

Usage:
    python project-register.py --register "Alfa" "/path/to/project"
    python project-register.py --register "Alfa" "/path" "Description here"
    python project-register.py --list
    python project-register.py --search "alfa"
    python project-register.py --status

Cross-platform: Works on Windows, Linux, macOS
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import bridge for memory
try:
    from session_bridge import SessionBridge
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False

# Import wiki populate
try:
    from wiki_populate import create_wiki_page
    WIKI_AVAILABLE = True
except ImportError:
    WIKI_AVAILABLE = False

# Registry path
REGISTRY_PATH = Path(__file__).parent.parent / ".context" / "projects" / "_registry.md"
MEMORY_PATH = Path.home() / ".pa-framework" / "memory" / "projects.json"


class ProjectRegistry:
    """
    Project registry that syncs to multiple sources:
    - SQLite (via SessionBridge)
    - Wiki (via wiki_populate)
    - Registry markdown file
    - JSON backup
    """
    
    def __init__(self):
        """Initialize registry"""
        self.registry_path = REGISTRY_PATH
        self.memory_path = MEMORY_PATH
        
        # Ensure paths exist
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory JSON if needed
        if not self.memory_path.exists():
            self.memory_path.write_text(json.dumps({"projects": []}))
        
        # Initialize bridge if available
        if BRIDGE_AVAILABLE:
            self.bridge = SessionBridge()
            if not self.bridge.current_session:
                self.bridge.start_session(metadata={"type": "project_registry"})
        else:
            self.bridge = None
    
    def register(
        self,
        name: str,
        path: str,
        description: Optional[str] = None,
        tags: Optional[list] = None,
        url: Optional[str] = None
    ) -> Dict:
        """
        Register a project in all memory systems.
        
        Args:
            name: Project name
            path: Project path
            description: Optional description
            tags: Optional tags list
            url: Optional URL
            
        Returns:
            Registration result
        """
        timestamp = datetime.now()
        
        # 1. Register in SessionBridge (SQLite)
        if self.bridge:
            self.bridge.register_project(name, path, description)
        
        # 2. Register in Wiki
        if WIKI_AVAILABLE:
            wiki_content = f"""# Project: {name}

| Campo | Valor |
|-------|-------|
| **Name** | {name} |
| **Path** | {path} |
| **Registered** | {timestamp.isoformat()} |
| **Description** | {description or 'No description provided'} |
| **URL** | {url or 'N/A'} |
| **Tags** | {tags or []} |

## Notes

This project is tracked in PA Framework memory. All sessions mentioning this project
will be searchable via the memory system.

## Quick Links

- [Project Directory]({path})
- [Related Sessions](../tasks/)
"""
            create_wiki_page(
                title=f"Project {name}",
                content=wiki_content,
                category="projects",
                tags=tags or ["project", name.lower()],
                source="project-register.py"
            )
        
        # 3. Update registry markdown
        self._update_registry_md(name, path, description, timestamp)
        
        # 4. Update memory JSON
        self._update_memory_json(name, path, description, timestamp)
        
        return {
            "success": True,
            "name": name,
            "path": path,
            "registered_at": timestamp.isoformat(),
            "sources": ["registry", "wiki", "memory", "sqlite"]
        }
    
    def _update_registry_md(self, name: str, path: str, description: Optional[str], timestamp: datetime):
        """Update registry markdown file"""
        
        entry = f"""

## {name}

| Campo | Valor |
|-------|-------|
| **Path** | `{path}` |
| **Registered** | {timestamp.isoformat()} |
| **Description** | {description or 'No description'} |
| **Status** | Active |

"""
        
        current = ""
        if self.registry_path.exists():
            current = self.registry_path.read_text()
        
        # Check if already registered
        if name.lower() in current.lower():
            print(f"[PROJECT] Already registered: {name}")
            return
        
        # Add header if empty
        if not current or current.strip() == "":
            current = "# Projects Registry\n\nThis file tracks all registered projects in PA Framework.\n\n---\n"
        
        self.registry_path.write_text(current + entry)
    
    def _update_memory_json(self, name: str, path: str, description: Optional[str], timestamp: datetime):
        """Update memory JSON file"""
        
        data = json.loads(self.memory_path.read_text())
        
        # Check if already exists
        for project in data["projects"]:
            if project["name"].lower() == name.lower():
                project["updated_at"] = timestamp.isoformat()
                if description:
                    project["description"] = description
                self.memory_path.write_text(json.dumps(data, indent=2))
                return
        
        # Add new project
        data["projects"].append({
            "name": name,
            "path": path,
            "description": description or "",
            "registered_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
        })
        
        self.memory_path.write_text(json.dumps(data, indent=2))
    
    def list_projects(self) -> list:
        """List all registered projects"""
        
        projects = []
        
        # From JSON memory
        if self.memory_path.exists():
            data = json.loads(self.memory_path.read_text())
            projects.extend(data.get("projects", []))
        
        # From registry markdown (parse)
        if self.registry_path.exists():
            content = self.registry_path.read_text()
            # Parse markdown entries (## Name)
            import re
            entries = re.findall(r'## (.+)\n\n\| .+ \| .+ |\n.*\| \*\*Path\*\* \| `([^`]+)`', content)
            for name, path in entries:
                # Check if already in list
                if not any(p["name"].lower() == name.lower() for p in projects):
                    projects.append({
                        "name": name,
                        "path": path,
                        "source": "registry_md"
                    })
        
        return projects
    
    def search(self, query: str) -> list:
        """Search projects by name or path"""
        
        query_lower = query.lower()
        results = []
        
        for project in self.list_projects():
            if query_lower in project.get("name", "").lower() or query_lower in project.get("path", "").lower():
                results.append(project)
        
        return results
    
    def get_project(self, name: str) -> Optional[Dict]:
        """Get specific project by name"""
        
        for project in self.list_projects():
            if project.get("name", "").lower() == name.lower():
                return project
        
        return None
    
    def get_stats(self) -> Dict:
        """Get registry statistics"""
        
        projects = self.list_projects()
        
        return {
            "total_projects": len(projects),
            "registry_path": str(self.registry_path),
            "memory_path": str(self.memory_path),
            "wiki_available": WIKI_AVAILABLE,
            "bridge_available": BRIDGE_AVAILABLE,
            "projects": [p["name"] for p in projects]
        }


def main():
    """CLI interface"""
    
    registry = ProjectRegistry()
    
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCurrent projects:")
        for p in registry.list_projects():
            print(f"  - {p.get('name')}: {p.get('path')}")
        return
    
    arg = sys.argv[1]
    
    if arg == "--register" and len(sys.argv) >= 4:
        name = sys.argv[2]
        path = sys.argv[3]
        description = sys.argv[4] if len(sys.argv) > 4 else None
        
        result = registry.register(name, path, description)
        print(f"[PROJECT] Registered: {name}")
        print(f"[PROJECT] Path: {path}")
        print(json.dumps(result, indent=2))
        
    elif arg == "--list":
        projects = registry.list_projects()
        print(f"[PROJECT] {len(projects)} registered:")
        for p in projects:
            print(f"\n  {p.get('name')}")
            print(f"    Path: {p.get('path')}")
            if p.get('description'):
                print(f"    Description: {p.get('description')}")
        
    elif arg == "--search" and len(sys.argv) > 2:
        query = sys.argv[2]
        results = registry.search(query)
        print(f"[PROJECT] Search '{query}': {len(results)} results")
        for r in results:
            print(f"  - {r.get('name')}: {r.get('path')}")
        
    elif arg == "--get" and len(sys.argv) > 2:
        name = sys.argv[2]
        project = registry.get_project(name)
        if project:
            print(f"[PROJECT] Found: {name}")
            print(json.dumps(project, indent=2))
        else:
            print(f"[PROJECT] Not found: {name}")
        
    elif arg == "--status":
        stats = registry.get_stats()
        print("[PROJECT] Registry Status:")
        print(json.dumps(stats, indent=2))
        
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
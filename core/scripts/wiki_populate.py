#!/usr/bin/env python3
"""
Wiki Populate - Populate LLM-Wiki with real content from codebase

The LLM-Wiki was EMPTY because nothing was populating it.
This script extracts knowledge from the codebase and creates wiki pages.

Usage:
    python wiki-populate.py --all          # Populate all sources
    python wiki-populate.py --projects     # Projects only
    python wiki-populate.py --skills       # Skills only
    python wiki-populate.py --status       # Show wiki status

Cross-platform: Works on Windows, Linux, macOS
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Wiki root location
WIKI_ROOT = Path(__file__).parent.parent / "memory" / "wiki"
PROJECT_ROOT = Path(__file__).parent.parent.parent


def create_wiki_page(
    title: str,
    content: str,
    category: str = "general",
    tags: Optional[List[str]] = None,
    source: Optional[str] = None
) -> Path:
    """
    Create wiki page with proper frontmatter.
    
    Args:
        title: Page title
        content: Page content (markdown)
        category: Category folder (projects, skills, tasks, etc.)
        tags: List of tags
        source: Source file this was extracted from
        
    Returns:
        Path to created page
    """
    category_path = WIKI_ROOT / category
    category_path.mkdir(parents=True, exist_ok=True)
    
    # Sanitize title for filename
    filename = title.lower().replace(" ", "-").replace("/", "-") + ".md"
    page_path = category_path / filename
    
    # Build frontmatter
    frontmatter = f"""---
title: {title}
created: {datetime.now().isoformat()}
category: {category}
tags: {tags or []}
source: {source or 'generated'}
---

"""
    
    page_path.write_text(frontmatter + content)
    return page_path


def populate_projects():
    """Populate wiki with project information"""
    
    projects_registry = PROJECT_ROOT / "core" / ".context" / "projects" / "_registry.md"
    projects_dir = PROJECT_ROOT / "core" / ".context" / "projects"
    
    pages_created = 0
    
    # Create projects category
    (WIKI_ROOT / "projects").mkdir(parents=True, exist_ok=True)
    
    # Import registry if exists
    if projects_registry.exists():
        content = projects_registry.read_text()
        create_wiki_page(
            title="Projects Registry",
            content=content,
            category="projects",
            tags=["registry", "projects"],
            source=str(projects_registry)
        )
        pages_created += 1
    
    # Create individual project pages from project directories
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith("_"):
            # Check for project README or main file
            readme = project_dir / "README.md"
            if readme.exists():
                create_wiki_page(
                    title=f"Project {project_dir.name}",
                    content=readme.read_text(),
                    category="projects",
                    tags=["project", project_dir.name],
                    source=str(readme)
                )
                pages_created += 1
    
    return pages_created


def populate_tasks():
    """Populate wiki with tasks/pendientes information"""
    
    tasks_files = [
        PROJECT_ROOT / "core" / ".context" / "codebase" / "recordatorios.md",
        PROJECT_ROOT / "core" / ".context" / "codebase" / "TODO.md",
        PROJECT_ROOT / "TODO.md",
    ]
    
    pages_created = 0
    (WIKI_ROOT / "tasks").mkdir(parents=True, exist_ok=True)
    
    for task_file in tasks_files:
        if task_file.exists():
            content = task_file.read_text()
            title = f"Tareas {task_file.stem}"
            
            create_wiki_page(
                title=title,
                content=content,
                category="tasks",
                tags=["tasks", "pendientes", task_file.stem],
                source=str(task_file)
            )
            pages_created += 1
    
    return pages_created


def populate_skills():
    """Populate wiki with skills information"""
    
    skills_dir = PROJECT_ROOT / "skills"
    pages_created = 0
    (WIKI_ROOT / "skills").mkdir(parents=True, exist_ok=True)
    
    if not skills_dir.exists():
        return 0
    
    # Create skills index
    skills_list = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                skills_list.append(f"- **{skill_dir.name}**: {skill_md.read_text()[:200]}...")
                
                # Create individual skill page
                create_wiki_page(
                    title=f"Skill {skill_dir.name}",
                    content=skill_md.read_text(),
                    category="skills",
                    tags=["skill", skill_dir.name],
                    source=str(skill_md)
                )
                pages_created += 1
    
    # Create skills index page
    if skills_list:
        create_wiki_page(
            title="Skills Available",
            content="# Skills Available\n\n" + "\n".join(skills_list),
            category="skills",
            tags=["index", "skills"],
            source="skills directory"
        )
        pages_created += 1
    
    return pages_created


def populate_agents():
    """Populate wiki with agents information"""
    
    agents_dir = PROJECT_ROOT / "agents"
    pages_created = 0
    (WIKI_ROOT / "agents").mkdir(parents=True, exist_ok=True)
    
    if not agents_dir.exists():
        return 0
    
    agents_list = []
    for agent_file in agents_dir.glob("*.md"):
        if agent_file.name != "README.md":
            content = agent_file.read_text()
            agent_name = agent_file.stem
            
            agents_list.append(f"- **{agent_name}**")
            
            create_wiki_page(
                title=f"Agent {agent_name}",
                content=content,
                category="agents",
                tags=["agent", agent_name],
                source=str(agent_file)
            )
            pages_created += 1
    
    # Create agents index
    if agents_list:
        create_wiki_page(
            title="Agents Available",
            content="# Agents Available\n\n" + "\n".join(agents_list),
            category="agents",
            tags=["index", "agents"],
            source="agents directory"
        )
        pages_created += 1
    
    return pages_created


def populate_errors():
    """Populate wiki with error history and playbooks"""
    
    errors_dir = PROJECT_ROOT / "core" / ".context" / "knowledge" / "errors"
    playbooks_dir = PROJECT_ROOT / "playbooks"
    
    pages_created = 0
    (WIKI_ROOT / "errors").mkdir(parents=True, exist_ok=True)
    
    # Error log
    error_log = errors_dir / "error-log.json"
    if error_log.exists():
        import json
        try:
            errors = json.loads(error_log.read_text())
            content = "# Error History\n\n"
            for err in errors.get("errors", [])[:10]:  # Last 10 errors
                content += f"## {err.get('type', 'Unknown')}\n\n"
                content += f"- **ID**: {err.get('id', 'N/A')}\n"
                content += f"- **Timestamp**: {err.get('timestamp', 'N/A')}\n"
                content += f"- **Status**: {err.get('status', 'unknown')}\n\n"
            
            create_wiki_page(
                title="Error History",
                content=content,
                category="errors",
                tags=["errors", "history"],
                source=str(error_log)
            )
            pages_created += 1
        except json.JSONDecodeError:
            pass
    
    # Playbooks
    if playbooks_dir.exists():
        for playbook in playbooks_dir.glob("*.md"):
            create_wiki_page(
                title=f"Playbook {playbook.stem}",
                content=playbook.read_text(),
                category="errors",
                tags=["playbook", playbook.stem],
                source=str(playbook)
            )
            pages_created += 1
    
    return pages_created


def populate_framework_status():
    """Populate wiki with framework status"""
    
    status_files = [
        PROJECT_ROOT / "AGENTS-lite.md",
        PROJECT_ROOT / "ROADMAP.md",
        PROJECT_ROOT / "CHANGELOG.md",
    ]
    
    pages_created = 0
    (WIKI_ROOT / "system").mkdir(parents=True, exist_ok=True)
    
    for status_file in status_files:
        if status_file.exists():
            create_wiki_page(
                title=f"Framework {status_file.stem}",
                content=status_file.read_text(),
                category="system",
                tags=["framework", status_file.stem],
                source=str(status_file)
            )
            pages_created += 1
    
    return pages_created


def populate_all():
    """Populate wiki with all sources"""
    
    print("[WIKI] Starting population...")
    print(f"[WIKI] Root: {WIKI_ROOT}")
    
    total_pages = 0
    
    results = {
        "projects": populate_projects(),
        "tasks": populate_tasks(),
        "skills": populate_skills(),
        "agents": populate_agents(),
        "errors": populate_errors(),
        "system": populate_framework_status(),
    }
    
    for category, count in results.items():
        print(f"[WIKI] {category}: {count} pages")
        total_pages += count
    
    print(f"[WIKI] Total pages created: {total_pages}")
    
    # Update wiki index
    update_wiki_index()
    
    return total_pages


def update_wiki_index():
    """Update wiki index page with all categories"""
    
    index_path = WIKI_ROOT / "index.md"
    
    content = "# PA Framework Wiki Index\n\n"
    content += f"**Last updated**: {datetime.now().isoformat()}\n\n"
    
    # Count pages per category
    categories = {}
    for category_dir in WIKI_ROOT.iterdir():
        if category_dir.is_dir():
            count = len(list(category_dir.glob("*.md")))
            categories[category_dir.name] = count
    
    content += "## Categories\n\n"
    content += "| Category | Pages |\n"
    content += "|----------|-------|\n"
    
    for cat, count in sorted(categories.items()):
        content += f"| {cat} | {count} |\n"
    
    content += "\n## Quick Links\n\n"
    content += "- [Projects Registry](projects/projects-registry.md)\n"
    content += "- [Skills Available](skills/skills-available.md)\n"
    content += "- [Agents Available](agents/agents-available.md)\n"
    content += "- [Tasks](tasks/)\n"
    content += "- [Error History](errors/error-history.md)\n"
    content += "- [Framework Status](system/)\n"
    
    index_path.write_text(content)
    print(f"[WIKI] Index updated")


def show_wiki_status():
    """Show current wiki status"""
    
    print("[WIKI] Status Report")
    print(f"[WIKI] Root: {WIKI_ROOT}")
    
    if not WIKI_ROOT.exists():
        print("[WIKI] Wiki not initialized")
        return
    
    total_pages = 0
    
    print("\n| Category | Pages | Files |")
    print("|----------|-------|-------|")
    
    for category_dir in WIKI_ROOT.iterdir():
        if category_dir.is_dir():
            pages = list(category_dir.glob("*.md"))
            count = len(pages)
            total_pages += count
            print(f"| {category_dir.name} | {count} | {', '.join(p.name for p in pages[:3])}... |")
    
    print(f"\n**Total pages**: {total_pages}")
    
    # Check for empty categories
    empty = []
    for category_dir in WIKI_ROOT.iterdir():
        if category_dir.is_dir() and len(list(category_dir.glob("*.md"))) == 0:
            empty.append(category_dir.name)
    
    if empty:
        print(f"\n⚠️ Empty categories: {', '.join(empty)}")


def main():
    """CLI interface"""
    
    if len(sys.argv) < 2:
        print(__doc__)
        populate_all()
        return
    
    arg = sys.argv[1]
    
    if arg == "--all":
        populate_all()
        
    elif arg == "--projects":
        count = populate_projects()
        print(f"[WIKI] Created {count} project pages")
        
    elif arg == "--skills":
        count = populate_skills()
        print(f"[WIKI] Created {count} skill pages")
        
    elif arg == "--agents":
        count = populate_agents()
        print(f"[WIKI] Created {count} agent pages")
        
    elif arg == "--tasks":
        count = populate_tasks()
        print(f"[WIKI] Created {count} task pages")
        
    elif arg == "--errors":
        count = populate_errors()
        print(f"[WIKI] Created {count} error pages")
        
    elif arg == "--status":
        show_wiki_status()
        
    elif arg == "--index":
        update_wiki_index()
        
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
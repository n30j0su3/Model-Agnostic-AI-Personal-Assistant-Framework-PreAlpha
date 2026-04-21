#!/usr/bin/env python3
"""
PA Framework — Knowledge Import
================================
Importa sesiones y conocimiento desde backups:
- JSON exports
- Portable .pa-export files
- Markdown session files

API:
    import_knowledge(source_path, merge=True, skip_existing=False)
    import_from_json(source_path, merge=True)
    import_from_portable(source_path, extract_dir=None)
    import_from_markdown(source_dir, merge=True)

Usage:
    python core/scripts/knowledge_import.py backup.json --merge
    python core/scripts/knowledge_import.py backup.pa-export
    python core/scripts/knowledge_import.py ./sessions-backup/ --from-markdown
    python core/scripts/knowledge_import.py backup.json --dry-run

Autor: FreakingJSON-PA Framework
Version: 1.0.0 (Phase 5 Workstream 2)
"""

import argparse
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONTEXT_DIR = REPO_ROOT / "core" / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "sessions-index.json"


class KnowledgeImporter:
    """
    Import sessions and knowledge from various formats.
    """

    def __init__(self):
        self.index_data: Dict = {}
        self.existing_sessions: Dict[str, Dict] = {}
        self._load_index()

    def _load_index(self):
        """Load existing sessions index."""
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                    self.index_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.index_data = {"sessions": []}
        else:
            self.index_data = {"sessions": []}

        # Build lookup by ID
        self.existing_sessions = {
            s.get("id", ""): s for s in self.index_data.get("sessions", [])
        }

    def _save_index(self):
        """Save sessions index."""
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        self.index_data["last_updated"] = datetime.now().isoformat()
        self.index_data["total_sessions"] = len(self.index_data.get("sessions", []))
        
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.index_data, f, indent=2, ensure_ascii=False)

    def import_from_json(
        self,
        source_path: Path,
        merge: bool = True,
        skip_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import sessions from JSON export.

        Args:
            source_path: Path to JSON export file
            merge: Merge with existing index
            skip_existing: Skip sessions that already exist

        Returns:
            Import statistics
        """
        stats = {
            "source": str(source_path),
            "format": "json",
            "sessions_imported": 0,
            "sessions_skipped": 0,
            "sessions_updated": 0,
            "errors": []
        }

        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            stats["errors"].append(f"Failed to read file: {e}")
            return stats

        sessions_to_import = import_data.get("sessions", [])

        for session in sessions_to_import:
            session_id = session.get("id", "")
            if not session_id:
                stats["errors"].append("Session missing ID, skipping")
                continue

            # Check if session exists
            if session_id in self.existing_sessions:
                if skip_existing:
                    stats["sessions_skipped"] += 1
                    continue
                else:
                    # Update existing
                    if merge:
                        self._update_session_in_index(session)
                        stats["sessions_updated"] += 1
                    continue

            # Add new session
            if merge:
                self._add_session_to_index(session)
            stats["sessions_imported"] += 1

            # Import session content if present
            content = session.get("content")
            if content:
                self._save_session_content(session_id, content)

        if merge:
            self._save_index()

        return stats

    def import_from_portable(
        self,
        source_path: Path,
        extract_dir: Optional[Path] = None,
        merge: bool = True,
        skip_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import from .pa-export portable format.

        Args:
            source_path: Path to .pa-export file
            extract_dir: Directory to extract to (default: sessions dir)
            merge: Merge with existing index
            skip_existing: Skip existing sessions

        Returns:
            Import statistics
        """
        stats = {
            "source": str(source_path),
            "format": "pa-export",
            "sessions_imported": 0,
            "sessions_skipped": 0,
            "sessions_updated": 0,
            "files_extracted": 0,
            "errors": []
        }

        if not source_path.exists():
            stats["errors"].append(f"File not found: {source_path}")
            return stats

        extract_dir = extract_dir or SESSIONS_DIR
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(source_path, 'r') as zf:
                # Extract manifest
                try:
                    manifest = json.loads(zf.read("manifest.json"))
                    stats["manifest"] = manifest
                except KeyError:
                    stats["errors"].append("No manifest.json found in archive")

                # Extract sessions index
                try:
                    index_json = zf.read("sessions-index.json")
                    index_data = json.loads(index_json)
                    sessions_to_import = index_data.get("sessions", [])
                except KeyError:
                    stats["errors"].append("No sessions-index.json found in archive")
                    return stats

                # Process each session
                for session in sessions_to_import:
                    session_id = session.get("id", "")
                    if not session_id:
                        continue

                    # Check if exists
                    if session_id in self.existing_sessions:
                        if skip_existing:
                            stats["sessions_skipped"] += 1
                            continue
                        else:
                            if merge:
                                self._update_session_in_index(session)
                                stats["sessions_updated"] += 1
                            continue

                    # Add to index
                    if merge:
                        self._add_session_to_index(session)
                    stats["sessions_imported"] += 1

                    # Extract session content
                    content_path = f"sessions/{session_id}.md"
                    try:
                        content = zf.read(content_path).decode('utf-8')
                        self._save_session_content(session_id, content)
                        stats["files_extracted"] += 1
                    except KeyError:
                        pass  # Content not in archive

                # Extract metadata if present
                try:
                    metadata = json.loads(zf.read("metadata.json"))
                    stats["metadata"] = metadata
                except KeyError:
                    pass

        except zipfile.BadZipFile as e:
            stats["errors"].append(f"Invalid archive: {e}")
            return stats

        if merge:
            self._save_index()

        return stats

    def import_from_markdown(
        self,
        source_dir: Path,
        merge: bool = True,
        skip_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import sessions from Markdown files.

        Args:
            source_dir: Directory containing .md session files
            merge: Merge with existing index
            skip_existing: Skip existing sessions

        Returns:
            Import statistics
        """
        stats = {
            "source": str(source_dir),
            "format": "markdown",
            "sessions_imported": 0,
            "sessions_skipped": 0,
            "sessions_updated": 0,
            "files_processed": 0,
            "errors": []
        }

        if not source_dir.exists():
            stats["errors"].append(f"Directory not found: {source_dir}")
            return stats

        # Find all session files (YYYY-MM-DD.md pattern)
        import re
        session_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\.md$")

        for md_file in source_dir.glob("*.md"):
            match = session_pattern.match(md_file.name)
            if not match:
                continue

            stats["files_processed"] += 1
            session_id = match.group(1)

            # Check if exists
            if session_id in self.existing_sessions:
                if skip_existing:
                    stats["sessions_skipped"] += 1
                    continue

            # Read content
            try:
                content = md_file.read_text(encoding='utf-8')
            except IOError as e:
                stats["errors"].append(f"Failed to read {md_file.name}: {e}")
                continue

            # Copy to sessions directory
            dest_file = SESSIONS_DIR / f"{session_id}.md"
            SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(md_file, dest_file)
            except IOError as e:
                stats["errors"].append(f"Failed to copy {md_file.name}: {e}")
                continue

            # Create/update index entry
            session_entry = self._parse_session_markdown(session_id, content)

            if session_id in self.existing_sessions:
                if merge:
                    self._update_session_in_index(session_entry)
                    stats["sessions_updated"] += 1
            else:
                if merge:
                    self._add_session_to_index(session_entry)
                stats["sessions_imported"] += 1

        if merge:
            self._save_index()

        return stats

    def _parse_session_markdown(self, session_id: str, content: str) -> Dict:
        """Parse Markdown content to create session index entry."""
        import re

        # Extract title (first H1)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f"Session {session_id}"

        # Extract summary (first paragraph after title)
        lines = content.split("\n")
        summary = ""
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith("#"):
                summary = line[:150]
                break

        # Extract topics (from content patterns)
        topics = []
        topic_patterns = [
            r"##\s+Temas.*?\n(.+?)(?=\n##|\Z)",
            r"topics?:\s*\[?([^\]]+)\]?",
        ]
        for pattern in topic_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1)
                bullets = re.findall(r"[-*]\s*\[?\s*([^\]]+?)\s*\]?\s*(?:\n|$)", text)
                topics.extend([b.strip().lower().replace(" ", "-") for b in bullets if b.strip()])

        # Determine type
        content_lower = content.lower()
        session_type = "other"
        if any(w in content_lower for w in ["fix", "bug", "error"]):
            session_type = "bugfix"
        elif any(w in content_lower for w in ["feature", "implement"]):
            session_type = "features"
        elif any(w in content_lower for w in ["research", "analysis"]):
            session_type = "research"

        # Calculate word count
        word_count = len(content.split())

        return {
            "id": session_id,
            "date": session_id,
            "time_start": "--:--",
            "time_end": None,
            "title": title,
            "summary": summary,
            "topics": topics[:10],
            "type": session_type,
            "stats": {
                "interactions": 0,
                "files_modified": 0,
                "decisions": 0,
                "lsp_errors": 0,
                "word_count": word_count
            },
            "highlights": [],
            "file_path": f"sessions/{session_id}.md",
            "status": "imported"
        }

    def _add_session_to_index(self, session: Dict):
        """Add session to index."""
        if "sessions" not in self.index_data:
            self.index_data["sessions"] = []

        self.index_data["sessions"].append(session)
        self.existing_sessions[session.get("id", "")] = session

    def _update_session_in_index(self, session: Dict):
        """Update existing session in index."""
        session_id = session.get("id", "")
        for i, existing in enumerate(self.index_data.get("sessions", [])):
            if existing.get("id") == session_id:
                self.index_data["sessions"][i] = session
                self.existing_sessions[session_id] = session
                break

    def _save_session_content(self, session_id: str, content: str):
        """Save session content to file."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        session_file = SESSIONS_DIR / f"{session_id}.md"
        session_file.write_text(content, encoding='utf-8')

    def validate_import(
        self,
        source_path: Path,
        source_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate an import source without actually importing.

        Args:
            source_path: Path to import source
            source_format: Format hint ('json', 'pa-export', 'markdown')

        Returns:
            Validation results
        """
        result = {
            "valid": False,
            "source": str(source_path),
            "format": None,
            "sessions_count": 0,
            "new_sessions": 0,
            "existing_sessions": 0,
            "errors": [],
            "warnings": []
        }

        if not source_path.exists():
            result["errors"].append(f"Path not found: {source_path}")
            return result

        # Detect format
        if source_path.is_file():
            if source_path.suffix == '.json':
                result["format"] = 'json'
            elif source_path.suffix == '.pa-export':
                result["format"] = 'pa-export'
            else:
                # Try to detect from content
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        first_char = f.read(1)
                        if first_char == '{':
                            result["format"] = 'json'
                        else:
                            result["warnings"].append("Unknown file format")
                except IOError:
                    result["errors"].append("Cannot read file")
                    return result

        elif source_path.is_dir():
            result["format"] = 'markdown'

        if not result["format"]:
            result["errors"].append("Could not determine format")
            return result

        # Count sessions
        if result["format"] == 'json':
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions = data.get("sessions", [])
                result["sessions_count"] = len(sessions)
                for s in sessions:
                    if s.get("id") in self.existing_sessions:
                        result["existing_sessions"] += 1
                    else:
                        result["new_sessions"] += 1
            except (json.JSONDecodeError, IOError) as e:
                result["errors"].append(f"Invalid JSON: {e}")

        elif result["format"] == 'pa-export':
            try:
                with zipfile.ZipFile(source_path, 'r') as zf:
                    index_data = json.loads(zf.read("sessions-index.json"))
                sessions = index_data.get("sessions", [])
                result["sessions_count"] = len(sessions)
                for s in sessions:
                    if s.get("id") in self.existing_sessions:
                        result["existing_sessions"] += 1
                    else:
                        result["new_sessions"] += 1
            except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
                result["errors"].append(f"Invalid archive: {e}")

        elif result["format"] == 'markdown':
            import re
            pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\.md$")
            for md_file in source_path.glob("*.md"):
                if pattern.match(md_file.name):
                    result["sessions_count"] += 1
                    session_id = pattern.match(md_file.name).group(1)
                    if session_id in self.existing_sessions:
                        result["existing_sessions"] += 1
                    else:
                        result["new_sessions"] += 1

        result["valid"] = len(result["errors"]) == 0
        return result


def import_knowledge(
    source_path: str,
    merge: bool = True,
    skip_existing: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Main API function for importing knowledge.

    Args:
        source_path: Path to import source
        merge: Merge with existing data
        skip_existing: Skip sessions that already exist
        dry_run: Validate without importing

    Returns:
        Import statistics
    """
    importer = KnowledgeImporter()
    source = Path(source_path)

    if dry_run:
        return importer.validate_import(source)

    # Determine format and import
    if source.is_file():
        if source.suffix == '.json':
            return importer.import_from_json(source, merge=merge, skip_existing=skip_existing)
        elif source.suffix == '.pa-export':
            return importer.import_from_portable(source, merge=merge, skip_existing=skip_existing)
        else:
            # Try JSON first
            try:
                return importer.import_from_json(source, merge=merge, skip_existing=skip_existing)
            except json.JSONDecodeError:
                return {"error": f"Unsupported file format: {source.suffix}"}

    elif source.is_dir():
        return importer.import_from_markdown(source, merge=merge, skip_existing=skip_existing)

    else:
        return {"error": f"Invalid source path: {source_path}"}


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework Knowledge Import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python knowledge_import.py backup.json --merge
  python knowledge_import.py backup.pa-export
  python knowledge_import.py ./sessions-backup/ --from-markdown
  python knowledge_import.py backup.json --dry-run
  python knowledge_import.py backup.json --skip-existing
        """
    )

    parser.add_argument("source", help="Source file or directory to import")
    parser.add_argument("--merge", action="store_true", default=True,
                        help="Merge with existing data (default: true)")
    parser.add_argument("--no-merge", action="store_false", dest="merge",
                        help="Replace existing data")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip sessions that already exist")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate without importing")
    parser.add_argument("--from-markdown", action="store_true",
                        help="Force import from Markdown directory")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    importer = KnowledgeImporter()
    source = Path(args.source)

    print("=" * 50)
    print("Knowledge Import")
    print("=" * 50)
    print(f"Source: {source}")

    if args.dry_run:
        print("\n[DRY RUN] Validating import...\n")
        result = importer.validate_import(source)

        print(f"Valid: {result['valid']}")
        print(f"Format: {result.get('format', 'unknown')}")
        print(f"Total sessions: {result.get('sessions_count', 0)}")
        print(f"New sessions: {result.get('new_sessions', 0)}")
        print(f"Existing sessions: {result.get('existing_sessions', 0)}")

        if result.get('errors'):
            print("\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")

        if result.get('warnings'):
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")

        return

    # Perform import
    if args.from_markdown or source.is_dir():
        result = importer.import_from_markdown(
            source,
            merge=args.merge,
            skip_existing=args.skip_existing
        )
    elif source.suffix == '.pa-export':
        result = importer.import_from_portable(
            source,
            merge=args.merge,
            skip_existing=args.skip_existing
        )
    else:
        result = importer.import_from_json(
            source,
            merge=args.merge,
            skip_existing=args.skip_existing
        )

    # Print results
    print(f"\nFormat: {result.get('format', 'unknown')}")
    print(f"Sessions imported: {result.get('sessions_imported', 0)}")
    print(f"Sessions updated: {result.get('sessions_updated', 0)}")
    print(f"Sessions skipped: {result.get('sessions_skipped', 0)}")

    if result.get('files_extracted'):
        print(f"Files extracted: {result['files_extracted']}")

    if result.get('files_processed'):
        print(f"Files processed: {result['files_processed']}")

    if result.get('errors'):
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")

    print("\n" + "=" * 50)
    print("Import Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()

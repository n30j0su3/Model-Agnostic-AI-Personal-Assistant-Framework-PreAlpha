#!/usr/bin/env python3
"""
PA Framework — Knowledge Export
================================
Exporta sesiones y conocimiento a formatos portables:
- JSON (completo o resumido)
- Markdown (reportes legibles)
- Formato portable (.pa-export)

API:
    export_knowledge(output_dir, format='json', sessions=None, include_content=True)
    export_sessions_to_markdown(output_dir, date_range=None)
    create_portable_export(output_path, sessions=None)

Usage:
    python core/scripts/knowledge_export.py --output ./exports --format json
    python core/scripts/knowledge_export.py --output ./exports --format markdown
    python core/scripts/knowledge_export.py --portable backup.pa-export
    python core/scripts/knowledge_export.py --from 2026-03-01 --to 2026-03-31

Autor: FreakingJSON-PA Framework
Version: 1.0.0 (Phase 5 Workstream 2)
"""

import argparse
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONTEXT_DIR = REPO_ROOT / "core" / ".context"
SESSIONS_DIR = CONTEXT_DIR / "sessions"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "sessions-index.json"


class KnowledgeExporter:
    """
    Export sessions and knowledge to various formats.
    """

    def __init__(self):
        self.index_data: Dict = {}
        self._load_index()

    def _load_index(self):
        """Load the sessions index."""
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                    self.index_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.index_data = {"sessions": []}
        else:
            self.index_data = {"sessions": []}

    def _get_session_content(self, session_id: str) -> Optional[str]:
        """Load full content of a session file."""
        session_file = SESSIONS_DIR / f"{session_id}.md"
        if session_file.exists():
            try:
                return session_file.read_text(encoding='utf-8')
            except IOError:
                pass
        return None

    def _filter_sessions(
        self,
        sessions: List[Dict],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        session_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Filter sessions by date range or specific IDs."""
        result = sessions

        if session_ids:
            result = [s for s in result if s.get("id") in session_ids]

        if from_date:
            result = [s for s in result if s.get("id", "") >= from_date]

        if to_date:
            result = [s for s in result if s.get("id", "") <= to_date]

        return result

    def export_to_json(
        self,
        output_path: Path,
        sessions: Optional[List[Dict]] = None,
        include_content: bool = True,
        compact: bool = False
    ) -> Dict[str, Any]:
        """
        Export sessions to JSON format.

        Args:
            output_path: Output file path
            sessions: List of sessions to export (default: all)
            include_content: Include full session content
            compact: Use compact format (less indentation)

        Returns:
            Export statistics
        """
        if sessions is None:
            sessions = self.index_data.get("sessions", [])

        export_data = {
            "version": "1.0",
            "export_date": datetime.now().isoformat(),
            "format": "json",
            "total_sessions": len(sessions),
            "sessions": []
        }

        for session in sessions:
            session_export = session.copy()

            if include_content:
                content = self._get_session_content(session.get("id", ""))
                if content:
                    session_export["content"] = content

            export_data["sessions"].append(session_export)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            if compact:
                json.dump(export_data, f, ensure_ascii=False)
            else:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        return {
            "output_file": str(output_path),
            "sessions_exported": len(sessions),
            "format": "json",
            "file_size": output_path.stat().st_size if output_path.exists() else 0
        }

    def export_to_markdown(
        self,
        output_dir: Path,
        sessions: Optional[List[Dict]] = None,
        single_file: bool = False,
        include_toc: bool = True
    ) -> Dict[str, Any]:
        """
        Export sessions to Markdown format.

        Args:
            output_dir: Output directory
            sessions: List of sessions to export
            single_file: Export all sessions to single file
            include_toc: Include table of contents

        Returns:
            Export statistics
        """
        if sessions is None:
            sessions = self.index_data.get("sessions", [])

        output_dir.mkdir(parents=True, exist_ok=True)

        files_created = []

        if single_file:
            # Export all to single file
            output_file = output_dir / "sessions-export.md"
            content = self._generate_markdown_report(sessions, include_toc=include_toc)
            output_file.write_text(content, encoding='utf-8')
            files_created.append(str(output_file))
        else:
            # Export each session to separate file
            for session in sessions:
                session_id = session.get("id", "unknown")
                output_file = output_dir / f"{session_id}.md"

                content = self._generate_session_markdown(session)
                output_file.write_text(content, encoding='utf-8')
                files_created.append(str(output_file))

            # Also create index file
            index_file = output_dir / "INDEX.md"
            index_content = self._generate_index_markdown(sessions)
            index_file.write_text(index_content, encoding='utf-8')
            files_created.append(str(index_file))

        return {
            "output_directory": str(output_dir),
            "sessions_exported": len(sessions),
            "format": "markdown",
            "files_created": files_created,
            "single_file": single_file
        }

    def _generate_session_markdown(self, session: Dict) -> str:
        """Generate Markdown content for a single session."""
        session_id = session.get("id", "unknown")
        title = session.get("title", "Sin título")
        date = session.get("date", session_id)
        session_type = session.get("type", "other")
        topics = session.get("topics", [])
        stats = session.get("stats", {})
        highlights = session.get("highlights", [])
        summary = session.get("summary", "")

        # Load full content if available
        full_content = self._get_session_content(session_id)

        md = []
        md.append(f"# {title}")
        md.append("")
        md.append(f"**ID:** {session_id}")
        md.append(f"**Fecha:** {date}")
        md.append(f"**Tipo:** {session_type}")
        md.append(f"**Tags:** {', '.join(topics) if topics else 'Ninguno'}")
        md.append("")

        if stats:
            md.append("## Estadísticas")
            md.append("")
            md.append(f"- Palabras: {stats.get('word_count', 0)}")
            md.append(f"- Interacciones: {stats.get('interactions', 0)}")
            md.append(f"- Archivos modificados: {stats.get('files_modified', 0)}")
            md.append(f"- Decisiones: {stats.get('decisions', 0)}")
            md.append(f"- Errores LSP: {stats.get('lsp_errors', 0)}")
            md.append("")

        if summary:
            md.append("## Resumen")
            md.append("")
            md.append(summary)
            md.append("")

        if highlights:
            md.append("## Highlights")
            md.append("")
            for h in highlights:
                h_type = h.get("type", "info")
                h_text = h.get("text", "")
                md.append(f"- **[{h_type}]** {h_text}")
            md.append("")

        if full_content:
            md.append("---")
            md.append("")
            md.append("## Contenido Completo")
            md.append("")
            md.append(full_content)

        return "\n".join(md)

    def _generate_index_markdown(self, sessions: List[Dict]) -> str:
        """Generate index Markdown file."""
        md = []
        md.append("# Sessions Index")
        md.append("")
        md.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**Total Sessions:** {len(sessions)}")
        md.append("")

        # Group by month
        by_month: Dict[str, List[Dict]] = {}
        for session in sessions:
            session_id = session.get("id", "")
            if len(session_id) >= 7:
                month = session_id[:7]  # YYYY-MM
                if month not in by_month:
                    by_month[month] = []
                by_month[month].append(session)

        for month in sorted(by_month.keys(), reverse=True):
            md.append(f"## {month}")
            md.append("")
            md.append("| ID | Title | Type | Topics |")
            md.append("|-----|-------|------|--------|")

            for session in sorted(by_month[month], key=lambda x: x.get("id", ""), reverse=True):
                session_id = session.get("id", "")
                title = session.get("title", "Sin título")[:50]
                session_type = session.get("type", "other")
                topics = ", ".join(session.get("topics", []))[:30]
                md.append(f"| [{session_id}]({session_id}.md) | {title} | {session_type} | {topics} |")

            md.append("")

        return "\n".join(md)

    def _generate_markdown_report(self, sessions: List[Dict], include_toc: bool = True) -> str:
        """Generate a single Markdown report with all sessions."""
        md = []
        md.append("# PA Framework - Sessions Export")
        md.append("")
        md.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**Total Sessions:** {len(sessions)}")
        md.append("")

        if include_toc and len(sessions) > 1:
            md.append("## Table of Contents")
            md.append("")
            for i, session in enumerate(sessions, 1):
                session_id = session.get("id", "")
                title = session.get("title", "Sin título")
                md.append(f"{i}. [{session_id}] {title}")
            md.append("")
            md.append("---")
            md.append("")

        for session in sessions:
            md.append(self._generate_session_markdown(session))
            md.append("")
            md.append("---")
            md.append("")

        return "\n".join(md)

    def create_portable_export(
        self,
        output_path: Path,
        sessions: Optional[List[Dict]] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Create a portable .pa-export file (ZIP-based format).

        Args:
            output_path: Output file path (.pa-export extension)
            sessions: List of sessions to export
            include_metadata: Include metadata files

        Returns:
            Export statistics
        """
        if sessions is None:
            sessions = self.index_data.get("sessions", [])

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure .pa-export extension
        if output_path.suffix != '.pa-export':
            output_path = output_path.with_suffix('.pa-export')

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add manifest
            manifest = {
                "version": "1.0",
                "format": "pa-export",
                "created": datetime.now().isoformat(),
                "total_sessions": len(sessions),
                "framework_version": self._get_framework_version()
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

            # Add sessions index
            index_data = {
                "export_date": datetime.now().isoformat(),
                "sessions": sessions
            }
            zf.writestr("sessions-index.json", json.dumps(index_data, indent=2))

            # Add session content files
            for session in sessions:
                session_id = session.get("id", "")
                content = self._get_session_content(session_id)
                if content:
                    zf.writestr(f"sessions/{session_id}.md", content)

            # Add metadata
            if include_metadata:
                metadata = {
                    "export_info": {
                        "tool": "knowledge_export.py",
                        "version": "1.0.0",
                        "timestamp": datetime.now().isoformat()
                    },
                    "statistics": self._calculate_export_stats(sessions)
                }
                zf.writestr("metadata.json", json.dumps(metadata, indent=2))

        return {
            "output_file": str(output_path),
            "sessions_exported": len(sessions),
            "format": "pa-export",
            "file_size": output_path.stat().st_size if output_path.exists() else 0,
            "compressed": True
        }

    def _calculate_export_stats(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics for exported sessions."""
        if not sessions:
            return {}

        total_words = sum(s.get("stats", {}).get("word_count", 0) for s in sessions)
        total_files = sum(s.get("stats", {}).get("files_modified", 0) for s in sessions)
        total_decisions = sum(s.get("stats", {}).get("decisions", 0) for s in sessions)

        # Date range
        session_ids = [s.get("id", "") for s in sessions if s.get("id")]
        date_range = {
            "from": min(session_ids) if session_ids else None,
            "to": max(session_ids) if session_ids else None
        }

        # Type distribution
        type_counts: Dict[str, int] = {}
        for session in sessions:
            stype = session.get("type", "other")
            type_counts[stype] = type_counts.get(stype, 0) + 1

        return {
            "total_sessions": len(sessions),
            "total_words": total_words,
            "total_files_modified": total_files,
            "total_decisions": total_decisions,
            "date_range": date_range,
            "type_distribution": type_counts
        }

    def _get_framework_version(self) -> str:
        """Get framework version from VERSION file."""
        version_file = REPO_ROOT / "VERSION"
        if version_file.exists():
            try:
                return version_file.read_text(encoding='utf-8').strip()
            except IOError:
                pass
        return "unknown"


def export_knowledge(
    output_dir: str,
    format: str = 'json',
    sessions: Optional[List[str]] = None,
    include_content: bool = True,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main API function for exporting knowledge.

    Args:
        output_dir: Output directory or file path
        format: Export format ('json', 'markdown', 'portable')
        sessions: List of session IDs to export (None = all)
        include_content: Include full session content
        from_date: Start date filter
        to_date: End date filter

    Returns:
        Export statistics
    """
    exporter = KnowledgeExporter()

    # Filter sessions
    all_sessions = exporter.index_data.get("sessions", [])
    filtered_sessions = exporter._filter_sessions(
        all_sessions,
        from_date=from_date,
        to_date=to_date,
        session_ids=sessions
    )

    output_path = Path(output_dir)

    if format == 'json':
        if output_path.suffix != '.json':
            output_path = output_path / f"knowledge-export-{datetime.now().strftime('%Y%m%d')}.json"
        return exporter.export_to_json(
            output_path,
            sessions=filtered_sessions,
            include_content=include_content
        )

    elif format == 'markdown':
        return exporter.export_to_markdown(
            output_path,
            sessions=filtered_sessions,
            single_file=False
        )

    elif format == 'portable':
        if output_path.suffix != '.pa-export':
            output_path = output_path / f"knowledge-export-{datetime.now().strftime('%Y%m%d')}.pa-export"
        return exporter.create_portable_export(
            output_path,
            sessions=filtered_sessions
        )

    else:
        raise ValueError(f"Unknown format: {format}")


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework Knowledge Export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python knowledge_export.py --output ./exports --format json
  python knowledge_export.py --output ./exports --format markdown
  python knowledge_export.py --portable backup.pa-export
  python knowledge_export.py --from 2026-03-01 --to 2026-03-31 --format json
        """
    )

    parser.add_argument("--output", "-o", default="./exports", help="Output directory or file")
    parser.add_argument("--format", "-f", choices=['json', 'markdown', 'portable'], default='json',
                        help="Export format (default: json)")
    parser.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--portable", help="Create portable export (shorthand for --format portable)")
    parser.add_argument("--no-content", action="store_true", help="Exclude full session content")
    parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    parser.add_argument("--single-file", action="store_true", help="Single Markdown file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    exporter = KnowledgeExporter()

    # Filter sessions
    all_sessions = exporter.index_data.get("sessions", [])
    filtered_sessions = exporter._filter_sessions(
        all_sessions,
        from_date=args.from_date,
        to_date=args.to_date
    )

    if args.verbose:
        print(f"Exporting {len(filtered_sessions)} sessions...")
        if args.from_date:
            print(f"  From: {args.from_date}")
        if args.to_date:
            print(f"  To: {args.to_date}")

    output_path = Path(args.output)

    # Determine format
    export_format = args.format
    if args.portable:
        export_format = 'portable'
        output_path = Path(args.portable)

    # Perform export
    if export_format == 'json':
        if output_path.suffix != '.json' and not output_path.is_dir():
            output_path = output_path.with_suffix('.json')
        result = exporter.export_to_json(
            output_path,
            sessions=filtered_sessions,
            include_content=not args.no_content,
            compact=args.compact
        )

    elif export_format == 'markdown':
        result = exporter.export_to_markdown(
            output_path,
            sessions=filtered_sessions,
            single_file=args.single_file
        )

    elif export_format == 'portable':
        if output_path.suffix != '.pa-export':
            output_path = output_path.with_suffix('.pa-export')
        result = exporter.create_portable_export(
            output_path,
            sessions=filtered_sessions
        )

    else:
        print(f"[ERROR] Unknown format: {export_format}")
        return

    # Print results
    print("\n" + "=" * 50)
    print("Export Complete")
    print("=" * 50)
    print(f"Format: {result['format']}")
    print(f"Sessions exported: {result['sessions_exported']}")

    if 'output_file' in result:
        print(f"Output file: {result['output_file']}")
        print(f"File size: {result.get('file_size', 0):,} bytes")

    if 'output_directory' in result:
        print(f"Output directory: {result['output_directory']}")
        print(f"Files created: {len(result.get('files_created', []))}")

    if result.get('compressed'):
        print("Compression: enabled")

    print("=" * 50)


if __name__ == "__main__":
    main()

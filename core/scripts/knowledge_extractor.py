#!/usr/bin/env python3
"""
PA Framework - Knowledge Extractor Module
Dual output system (JSON + MD) for knowledge extraction from sessions.
Uses PatternDetector for parsing; handles file I/O and orchestration.

Usage:
    from knowledge_extractor import KnowledgeExtractor
    extractor = KnowledgeExtractor()
    results = extractor.extract_all_knowledge(session_file)
"""

import importlib
import json, re, sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_kpd = importlib.import_module("knowledge_pattern_detector")
PatternDetector = _kpd.PatternDetector
SessionContent = _kpd.SessionContent

if sys.platform == "win32" and sys.stdout.isatty():
    try:
                # v0.4.0-beta fix: reconfigure in-place (TextIOWrapper nuevo dejaba un wrapper
# huérfano que su GC cerraba → "I/O operation on closed file"/"lost sys.stderr" al salir)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONFIG_FILE = REPO_ROOT / "config" / "framework.yaml"
_RED, _END = "\033[91m", "\033[0m"

DEFAULT_CONFIG = {
    "enabled": True,
    "auto_detect": {"discoveries": True, "prompts": True, "ideas": True, "best_practices": True},
    "tags": {"discovery": "#discovery", "prompt_success": "#prompt-success",
             "idea": "#idea", "best_practice": "#best-practice"},
    "output": {
        "discoveries": "core/.context/knowledge/learning/discoveries.md",
        "prompts": "core/.context/knowledge/prompts/registry.json",
        "ideas": "core/.context/codebase/ideas.md",
        "best_practices": "core/.context/knowledge/learning/best-practices.md",
        "index": "core/.context/knowledge/knowledge-index.json",
    },
}


def _c(text: str, color: str) -> str:
    return f"{color}{text}{_END}"


def _safe_print(text: str, **kw):
    try:
        print(text, **kw)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "utf-8"
        print(text.encode(enc, errors="replace").decode(enc), **kw)


def _load_yaml_config(path: Path) -> Dict[str, Any]:
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return _parse_yaml_simple(path)
    except FileNotFoundError:
        return {}


def _parse_yaml_simple(path: Path) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    try:
        sec = sub = None
        for line in path.read_text(encoding="utf-8").split("\n"):
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("    ") and sec and sub:
                m = re.match(r"\s{4}(\w+):\s*(.+)", line)
                if m:
                    k, v = m.groups(); v = v.strip().strip('"').strip("'")
                    cfg[sec][sub][k] = v.lower() == "true" if v.lower() in ("true", "false") else v
            elif line.startswith("  ") and sec:
                m = re.match(r"\s{2}(\w+):\s*(.+)?", line)
                if m:
                    k, v = m.groups()
                    if v is None:
                        cfg[sec][k] = {}; sub = k
                    else:
                        v = v.strip().strip('"').strip("'")
                        cfg[sec][k] = v.lower() == "true" if v.lower() in ("true", "false") else v
                        sub = None
            elif ":" in line:
                k = line.split(":")[0].strip(); cfg[k] = {}; sec, sub = k, None
    except Exception:
        pass
    return cfg


class KnowledgeExtractor:
    """Dual output system for knowledge extraction from session files."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = self._load_config(config)
        self._paths = self._build_paths()
        for p in self._paths.values():
            p.parent.mkdir(parents=True, exist_ok=True)
        self._init_files()
        self._detector = PatternDetector(tags=self.config.get("tags"), auto_detect=self.config.get("auto_detect"))

    @property
    def discoveries_file(self): return self._paths["discoveries"]
    @property
    def prompts_file(self): return self._paths["prompts"]
    @property
    def ideas_file(self): return self._paths["ideas"]
    @property
    def best_practices_file(self): return self._paths["best_practices"]
    @property
    def index_file(self): return self._paths["index"]

    def _load_config(self, config: Optional[Dict]) -> Dict:
        if config: return {**DEFAULT_CONFIG, **config}
        yc = _load_yaml_config(CONFIG_FILE).get("knowledge_extraction", {})
        m = {**DEFAULT_CONFIG}
        for k in ("enabled", "auto_detect", "tags", "output"):
            if k in yc: m[k] = {**m[k], **yc[k]} if isinstance(m[k], dict) else yc[k]
        return m

    def _build_paths(self) -> Dict[str, Path]:
        out = self.config.get("output", DEFAULT_CONFIG["output"])
        return {k: REPO_ROOT / out.get(k, DEFAULT_CONFIG["output"][k]) for k in out}

    def _init_files(self):
        headers = {"discoveries": ("Discoveries Log", "Auto-generated discoveries log"),
                    "ideas": ("Ideas Log", "Auto-generated ideas log"),
                    "best_practices": ("Best Practices Log", "Auto-generated best practices log")}
        for key, (title, desc) in headers.items():
            if not self._paths[key].exists():
                self._write_md_header(self._paths[key], title, desc)
        if not self._paths["prompts"].exists():
            self._write_json(self._paths["prompts"], {"prompts": [], "last_updated": None})
        if not self._paths["index"].exists():
            self._write_json(self._paths["index"],
                             {"discoveries": 0, "prompts": 0, "ideas": 0, "best_practices": 0,
                              "last_extraction": None, "history": []})

    # --- File I/O ---
    def _write_md_header(self, p: Path, title: str, desc: str):
        try:
            p.write_text(f"# {title}\n\n> {desc}\n> Part of Knowledge Extraction System\n\n---\n\n", encoding="utf-8")
        except Exception as e: _safe_print(_c(f"[ERROR] {e}", _RED))

    def _write_json(self, p: Path, data: Dict):
        try: p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e: _safe_print(_c(f"[ERROR] {e}", _RED))

    def _read_json(self, p: Path) -> Dict:
        try: return json.loads(p.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError): return {}

    def _append_md(self, p: Path, content: str) -> bool:
        try:
            with open(p, "a", encoding="utf-8") as f: f.write(content)
            return True
        except Exception as e: _safe_print(_c(f"[ERROR] {e}", _RED)); return False

    def _get_tag(self, name: str) -> str:
        return self.config.get("tags", DEFAULT_CONFIG["tags"]).get(name, "")

    # --- Update methods ---
    def _write_md_entries(self, key: str, items: List[Dict], fmt_fn) -> bool:
        if not items: return True
        try:
            for item in items: self._append_md(self._paths[key], fmt_fn(item))
            return True
        except Exception as e: _safe_print(_c(f"[ERROR] {e}", _RED)); return False

    def update_discoveries_file(self, discoveries: List[Dict]) -> bool:
        tag = self._get_tag("discovery")
        def fmt(d):
            det = "automatica" if d.get("auto_detected") else f"tag {tag}"
            return (f"### {datetime.now():%Y-%m-%d}: [PENDIENTE VALIDACION] {d.get('title', 'Untitled')}\n\n"
                    f"> **Estado**: pendiente_validacion\n> **Extraido de**: sessions/{d.get('session_file', 'unknown')}#L{d.get('extracted_from', 0)}\n"
                    f"> **Deteccion**: {det}\n\n**Contexto**: {d.get('context', 'N/A')}\n\n"
                    f"**Descubrimiento**: {d.get('discovery', 'N/A')}\n\n**Impacto**: {d.get('impact', 'N/A')}\n\n---\n\n")
        return self._write_md_entries("discoveries", discoveries, fmt)

    def update_prompts_registry(self, prompts: List[Dict]) -> bool:
        if not prompts: return True
        try:
            reg = self._read_json(self._paths["prompts"]) or {"prompts": []}
            existing = {p.get("id") for p in reg.get("prompts", [])}
            for p in prompts:
                if p.get("id") not in existing: reg.setdefault("prompts", []).append(p)
            reg["last_updated"] = datetime.now().isoformat()
            self._write_json(self._paths["prompts"], reg); return True
        except Exception as e: _safe_print(_c(f"[ERROR] {e}", _RED)); return False

    def update_ideas_file(self, ideas: List[Dict]) -> bool:
        tag = self._get_tag("idea")
        def fmt(i):
            st = i.get("status", "pending")
            return (f"### {datetime.now():%Y-%m-%d}: [{'VALIDADA' if st == 'validated' else 'PENDIENTE'}] {i.get('title', 'Untitled')}\n\n"
                    f"> **Estado**: {st}\n> **Prioridad**: {i.get('priority', 'medium')}\n"
                    f"> **Extraido de**: session#L{i.get('extracted_from', 0)}\n> **Deteccion**: {'automatica' if i.get('auto_detected') else f'tag {tag}'}\n\n"
                    f"**Descripcion**: {i.get('description', 'N/A')}\n\n---\n\n")
        return self._write_md_entries("ideas", ideas, fmt)

    def update_best_practices_file(self, practices: List[Dict]) -> bool:
        tag = self._get_tag("best_practice")
        def fmt(p):
            st = p.get("status", "pending_validation")
            return (f"### {datetime.now():%Y-%m-%d}: [{'VALIDADA' if st == 'validated' else 'PENDIENTE VALIDACION'}] {p.get('title', 'Untitled')}\n\n"
                    f"> **Estado**: {st}\n> **Extraido de**: session#L{p.get('extracted_from', 0)}\n"
                    f"> **Deteccion**: {'automatica' if p.get('auto_detected') else f'tag {tag}'}\n\n"
                    f"**Contexto**: {p.get('context', 'N/A')}\n\n**Practica**: {p.get('practice', 'N/A')[:500]}\n\n"
                    f"**Beneficio**: {p.get('benefit', 'N/A')}\n\n---\n\n")
        return self._write_md_entries("best_practices", practices, fmt)

    def update_knowledge_index(self, stats: Dict) -> bool:
        try:
            idx = self._read_json(self._paths["index"]) or {}
            for k in ("discoveries", "prompts", "ideas", "best_practices"):
                idx.setdefault(k, 0); idx[k] += stats.get(k, 0)
            idx.setdefault("last_extraction", None); idx.setdefault("history", [])
            idx["last_extraction"] = datetime.now().isoformat()
            idx["history"].append({"timestamp": datetime.now().isoformat(), "session": stats.get("session_file", "unknown"),
                                   **{k: stats.get(k, 0) for k in ("discoveries", "prompts", "ideas", "best_practices")}})
            idx["history"] = idx["history"][-100:]
            self._write_json(self._paths["index"], idx); return True
        except Exception as e: _safe_print(_c(f"[ERROR] {e}", _RED)); return False

    # --- Main entry points (File-based) ---
    def extract_session_discoveries(self, sf: Path) -> List[Dict]:
        return self._detector.extract_discoveries(SessionContent(sf))
    def extract_successful_prompts(self, sf: Path) -> List[Dict]:
        return self._detector.extract_prompts(SessionContent(sf))
    def extract_validated_ideas(self, sf: Path) -> List[Dict]:
        return self._detector.extract_ideas(SessionContent(sf))
    def extract_best_practices(self, sf: Path) -> List[Dict]:
        return self._detector.extract_best_practices(SessionContent(sf))

    def extract_all_knowledge(self, session_file: Path) -> Dict:
        if not self.config.get("enabled", True):
            return {"discoveries": 0, "prompts": 0, "ideas": 0, "best_practices": 0,
                    "success": False, "session_file": str(session_file), "message": "Knowledge extraction disabled"}
        session = SessionContent(session_file)
        d, pr, i, bp = (self._detector.extract_discoveries(session), self._detector.extract_prompts(session),
                        self._detector.extract_ideas(session), self._detector.extract_best_practices(session))
        # Filter out any None items to prevent TypeError on assignment
        d = [x for x in d if x is not None]
        pr = [x for x in pr if x is not None]
        i = [x for x in i if x is not None]
        bp = [x for x in bp if x is not None]
        for items in (d, pr, i, bp):
            for item in items: item["session_file"] = session_file.name
        stats = {"discoveries": len(d), "prompts": len(pr), "ideas": len(i),
                 "best_practices": len(bp), "session_file": session_file.name}
        ok = all([self.update_discoveries_file(d), self.update_prompts_registry(pr),
                  self.update_ideas_file(i), self.update_best_practices_file(bp), self.update_knowledge_index(stats)])
        return {**stats, "success": ok}

    # --- SQLite-based entry points ---
    def extract_all_knowledge_from_session(self, session_obj, session_id: str = None) -> Dict:
        """Extract knowledge from a Session-like object (SQLite-backed).
        
        Uses duck typing - accepts any object with .raw and .lines properties.
        Designed for SessionContentSQLite adapter but works with any compatible object.
        
        Args:
            session_obj: Object with .raw and .lines properties (e.g., SessionContentSQLite)
            session_id: Optional session ID override (defaults to session_obj.name)
        
        Returns:
            Dict with extraction stats and success status
        """
        if not self.config.get("enabled", True):
            return {"discoveries": 0, "prompts": 0, "ideas": 0, "best_practices": 0,
                    "success": False, "session_id": session_id or getattr(session_obj, "name", "unknown"),
                    "message": "Knowledge extraction disabled"}
        
        # Duck typing: just need .raw and .lines
        d, pr, i, bp = (self._detector.extract_discoveries(session_obj),
                        self._detector.extract_prompts(session_obj),
                        self._detector.extract_ideas(session_obj),
                        self._detector.extract_best_practices(session_obj))
        
        # Filter None items
        d = [x for x in d if x is not None]
        pr = [x for x in pr if x is not None]
        i = [x for x in i if x is not None]
        bp = [x for x in bp if x is not None]
        
        sid = session_id or getattr(session_obj, "name", "unknown")
        for items in (d, pr, i, bp):
            for item in items: item["session_id"] = sid
        
        stats = {"discoveries": len(d), "prompts": len(pr), "ideas": len(i),
                 "best_practices": len(bp), "session_id": sid}
        
        ok = all([self.update_discoveries_file(d), self.update_prompts_registry(pr),
                  self.update_ideas_file(i), self.update_best_practices_file(bp), self.update_knowledge_index(stats)])
        return {**stats, "success": ok}


class SQLiteSessionContent:
    """
    Duck-typed adapter: makes a SQLite session (data/sessions.db) look like
    SessionContent (.raw / .lines) so PatternDetector can extract knowledge
    from captured conversations, not only from .md files (v0.3.9-alpha).
    """

    def __init__(self, session_id: str, messages: List[Dict]):
        self.session_id = session_id
        self.name = f"sqlite-{session_id[:8]}.md"
        lines = [f"# Session {session_id} (SQLite capture)"]
        for m in messages:
            ts = datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M")
            lines.append(f"\n## {m['role'].title()} [{ts}]")
            lines.append(m["content"])
        self._raw = "\n".join(lines)

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def lines(self) -> List[str]:
        return self._raw.split("\n")


def iter_sqlite_sessions(limit: int = 0) -> List[Dict]:
    """
    Read captured sessions from data/sessions.db (SessionBridge output).
    Returns a list of {"session_id", "messages": [...]} dicts.
    Empty list when the DB or the table does not exist (graceful).
    """
    import sqlite3

    db = REPO_ROOT / "data" / "sessions.db"
    if not db.exists():
        return []
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
    except sqlite3.Error:
        return []
    out: List[Dict] = []
    try:
        q = "SELECT session_id FROM sessions ORDER BY created_at DESC"
        if limit:
            q += f" LIMIT {int(limit)}"
        sids = [r["session_id"] for r in con.execute(q).fetchall()]
        for sid in sids:
            msgs = [
                dict(r) for r in con.execute(
                    "SELECT role, content, timestamp FROM session_messages "
                    "WHERE session_id = ? ORDER BY timestamp ASC",
                    (sid,),
                ).fetchall()
            ]
            if msgs:
                out.append({"session_id": sid, "messages": msgs})
    except sqlite3.Error:
        return []
    finally:
        con.close()
    return out


def extract_all_knowledge(session_file: Path) -> Dict:
    return KnowledgeExtractor().extract_all_knowledge(session_file)
def extract_session_discoveries(session_file: Path) -> List[Dict]:
    return KnowledgeExtractor().extract_session_discoveries(session_file)
def extract_successful_prompts(session_file: Path) -> List[Dict]:
    return KnowledgeExtractor().extract_successful_prompts(session_file)
def extract_validated_ideas(session_file: Path) -> List[Dict]:
    return KnowledgeExtractor().extract_validated_ideas(session_file)
def extract_best_practices(session_file: Path) -> List[Dict]:
    return KnowledgeExtractor().extract_best_practices(session_file)


# ============================================================================
# CLI (v0.3.9-alpha) — fixes the false-green in memory_pipeline:
# the pipeline runs `python knowledge_extractor.py` expecting a CLI that
# did not exist. Sources: --md (Markdown sessions) + --sqlite (captured).
# ============================================================================

def _cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="PA Framework — Knowledge Extractor (MD + SQLite, v0.3.9)",
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--md", action="store_true",
                     help="Extract from Markdown sessions only")
    src.add_argument("--sqlite", action="store_true",
                     help="Extract from SQLite captures only")
    parser.add_argument("--file", type=str, default=None,
                        help="Extract from a single .md session file")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max SQLite sessions to process (0 = all)")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-item output")
    args = parser.parse_args()

    ex = KnowledgeExtractor()
    totals = {"discoveries": 0, "prompts": 0, "ideas": 0, "best_practices": 0}
    ok_any = False

    # Single file mode
    if args.file:
        p = Path(args.file)
        if not p.exists():
            _safe_print(_c(f"[ERROR] File not found: {p}", _RED))
            return 1
        res = ex.extract_all_knowledge(p)
        ok_any = res.get("success", False)
        for k in totals:
            totals[k] += res.get(k, 0)
    else:
        # Markdown sessions (default when neither --md nor --sqlite)
        if not args.sqlite:
            sessions_dir = REPO_ROOT / "core" / ".context" / "sessions"
            if sessions_dir.exists():
                for sf in sorted(sessions_dir.glob("*.md")):
                    try:
                        res = ex.extract_all_knowledge(sf)
                        ok_any = ok_any or res.get("success", False)
                        for k in totals:
                            totals[k] += res.get(k, 0)
                    except Exception as e:
                        _safe_print(_c(f"[WARN] {sf.name}: {e}", _RED))
        # SQLite captures (default when neither flag given, or explicit --sqlite)
        if not args.md:
            for sess in iter_sqlite_sessions(limit=args.limit):
                adapter = SQLiteSessionContent(sess["session_id"], sess["messages"])
                try:
                    res = ex.extract_all_knowledge_from_session(
                        adapter, session_id=adapter.name
                    )
                    ok_any = ok_any or res.get("success", False)
                    for k in totals:
                        totals[k] += res.get(k, 0)
                except Exception as e:
                    _safe_print(_c(f"[WARN] {adapter.name}: {e}", _RED))

    if not args.quiet:
        _safe_print(
            "Knowledge extraction: "
            + ", ".join(f"{v} {k}" for k, v in totals.items())
            + ("" if ok_any else " [WARN: all sources failed]")
        )
    # Exit 0 when extraction ran on at least one source successfully
    return 0 if ok_any else 1


if __name__ == "__main__":
    sys.exit(_cli())

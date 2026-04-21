#!/usr/bin/env python3
"""
PA Framework - Knowledge Pattern Detector

Cross-session pattern analysis for recurring themes, topics, and errors.
Extracts knowledge items from individual sessions and detects patterns
across multiple sessions.

Part of Session-End Pipeline (§3.6 IMPLEMENTATION-PLAN-Phase3).

Usage:
    from knowledge_pattern_detector import PatternDetector

    detector = PatternDetector()
    patterns = detector.analyze_sessions(session_files)
    # Returns list of Pattern dicts with:
    #   pattern_type, description, frequency, sessions
"""

import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- Lazy-load decorator ---

def lazy_load(attr_name: str):
    """Decorator that defers file reading until first access."""
    def decorator(func):
        _cache_attr = f"_cached_{attr_name}"
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, _cache_attr) or getattr(self, _cache_attr) is None:
                setattr(self, _cache_attr, func(self, *args, **kwargs))
            return getattr(self, _cache_attr)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


# --- Tag definitions ---

TAGS = {
    "discovery": "#discovery",
    "prompt_success": "#prompt-success",
    "idea": "#idea",
    "best_practice": "#best-practice",
}

SECTION_HEADERS = {
    "discoveries": re.compile(r"^##\s+(Hallazgos|Discoveries)", re.IGNORECASE),
    "ideas": re.compile(r"^##\s+Ideas"),
    "solution": re.compile(r"^##\s+Soluci[oó]n", re.IGNORECASE),
}

SUCCESS_INDICATORS = [
    "funciono", "exitoso", "exito", "success",
    "[ok]", "correcto", "resolved", "solved",
]

VALIDATION_INDICATORS = [
    "[ok]", "validado", "aprobado", "approved",
    "aceptado", "confirmado",
]


# --- Session content helpers ---

class SessionContent:
    """Lazy-parsed representation of a session file."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self._raw: Optional[str] = None
        self._lines: Optional[List[str]] = None

    @property
    def raw(self) -> str:
        if self._raw is None:
            self._raw = self.path.read_text(encoding="utf-8")
        return self._raw

    @property
    def lines(self) -> List[str]:
        if self._lines is None:
            self._lines = self.raw.split("\n")
        return self._lines

    def invalidate(self):
        self._raw = None
        self._lines = None


# --- Pattern Detector ---

class PatternDetector:
    """
    Detects knowledge patterns within and across sessions.

    Single-session: extract discoveries, prompts, ideas, best practices.
    Cross-session: find recurring themes, topics, errors via analyze_sessions().
    """

    def __init__(self, tags: Optional[Dict[str, str]] = None,
                 auto_detect: Optional[Dict[str, bool]] = None):
        self.tags = tags or TAGS.copy()
        self.auto_detect = auto_detect or {
            "discoveries": True, "prompts": True,
            "ideas": True, "best_practices": True,
        }

    # --- Single-session extraction ---

    def extract_discoveries(self, session: SessionContent) -> List[Dict]:
        """Extract discoveries from a single session."""
        results: List[Dict] = []
        tag = self.tags.get("discovery", "")
        auto = self.auto_detect.get("discoveries", True)

        for i, line in enumerate(session.lines):
            if tag and tag in line:
                item = self._parse_tagged_block(session.lines, i, tag, "discovery")
                if item:
                    results.append(item)
                continue
            if auto:
                if SECTION_HEADERS["discoveries"].match(line):
                    results.extend(self._parse_list_section(session.lines, i + 1, "discovery"))
                if "descubrimiento:" in line.lower() or "discovery:" in line.lower():
                    item = self._parse_inline(session.lines, i,
                                              r"(?:descubrimiento|discovery)[:\s]+(.+)", "discovery")
                    if item:
                        results.append(item)
        return results

    def extract_prompts(self, session: SessionContent) -> List[Dict]:
        """Extract successful prompts from a single session."""
        results: List[Dict] = []
        tag = self.tags.get("prompt_success", "")
        auto = self.auto_detect.get("prompts", True)
        lines = session.lines

        code_start = None
        code_buf: List[str] = []

        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                if code_start is None:
                    code_start = i
                    code_buf = []
                else:
                    if auto and i + 1 < len(lines):
                        nxt = " ".join(lines[i + 1:min(i + 4, len(lines))]).lower()
                        if any(ind in nxt for ind in SUCCESS_INDICATORS):
                            results.append(self._code_block_prompt(code_buf, code_start))
                    code_start = None
                    code_buf = []
                continue
            if code_start is not None:
                code_buf.append(line)
            if tag and tag in line:
                item = self._parse_tagged_prompt(lines, i, tag)
                if item:
                    results.append(item)
        return results

    def extract_ideas(self, session: SessionContent) -> List[Dict]:
        """Extract validated ideas from a single session."""
        results: List[Dict] = []
        tag = self.tags.get("idea", "")
        auto = self.auto_detect.get("ideas", True)
        in_section = False

        for i, line in enumerate(session.lines):
            if line.startswith("## Ideas"):
                in_section = True
                continue
            if line.startswith("## ") and in_section:
                in_section = False

            if tag and tag in line:
                text = re.sub(r"^[-*\d.]+\s*", "", line.replace(tag, "").strip())
                if text:
                    results.append(self._make_item("idea", text, i, auto_detected=False,
                                                   extra={"priority": "medium", "status": "pending"}))
                continue
            if auto:
                low = line.lower()
                if any(v in low for v in VALIDATION_INDICATORS):
                    if line.strip().startswith(("-", "*", "1.", "2.", "3.")):
                        text = re.sub(r"\[ok\]|\[x\]", "", re.sub(r"^[-*\d.]+\s*", "", line.strip()),
                                      flags=re.IGNORECASE).strip()
                        if text:
                            results.append(self._make_item("idea", text, i, auto_detected=True,
                                                           extra={"priority": "high", "status": "validated"}))
                if in_section and line.strip().startswith(("-", "*")):
                    m = re.match(r"^[-*]\s*\[x\]\s*(.+)", line.strip(), re.IGNORECASE)
                    if m:
                        results.append(self._make_item("idea", m.group(1), i, auto_detected=True,
                                                       extra={"priority": "medium", "status": "validated"}))
        return results

    def extract_best_practices(self, session: SessionContent) -> List[Dict]:
        """Extract best practices from a single session."""
        results: List[Dict] = []
        tag = self.tags.get("best_practice", "")
        auto = self.auto_detect.get("best_practices", True)
        lines = session.lines

        for i, line in enumerate(lines):
            if tag and tag in line:
                ctx = " ".join(l.strip() for l in lines[max(0, i - 3):i])[:200]
                text = re.sub(r"^[-*\d.]+\s*", "", line.replace(tag, "").strip())
                if text:
                    results.append(self._make_item("best_practice", text, i,
                                                   auto_detected=False, context=ctx,
                                                   extra={"benefit": "To be documented"}))
                continue
            if auto:
                if SECTION_HEADERS["solution"].match(line):
                    sl = [l.strip() for l in lines[i+1:min(len(lines), i+15)]
                          if l.strip() and not l.startswith("## ")]
                    text = re.sub(r"\s+", " ", " ".join(sl))
                    if len(text) >= 20:
                        results.append(self._make_item("best_practice", text[:500], i,
                                                       auto_detected=True,
                                                       context="Auto-detected from Solución section",
                                                       extra={"benefit": "Resolved issue in session"}))
                if any(w in line.lower() for w in ("funciono", "worked", "resolved")):
                    if i > 0 and "```" in lines[i - 1]:
                        solution = self._extract_code_solution(lines, i)
                        if solution is not None:
                            results.append(solution)
        return results

    # --- Cross-session analysis ---

    def analyze_sessions(self, session_paths: List[Path]) -> List[Dict]:
        """
        Cross-session pattern analysis.

        Args:
            session_paths: List of session file paths to analyze.

        Returns:
            List of Pattern dicts, each containing:
                pattern_type: str (theme|topic|error|discovery|practice)
                description: str
                frequency: int
                sessions: list of session file names
        """
        if not session_paths:
            return []

        sessions = [SessionContent(p) for p in session_paths if p.exists()]
        if not sessions:
            return []

        # Collect all extracted items across sessions
        all_items: Dict[str, List[Dict]] = {
            "discoveries": [], "prompts": [], "ideas": [], "best_practices": [],
        }
        for s in sessions:
            all_items["discoveries"].extend(self.extract_discoveries(s))
            all_items["prompts"].extend(self.extract_prompts(s))
            all_items["ideas"].extend(self.extract_ideas(s))
            all_items["best_practices"].extend(self.extract_best_practices(s))

        patterns: List[Dict] = []

        # 1. Recurring themes from discoveries
        theme_patterns = self._find_recurring_text(
            [d.get("title", "") + " " + d.get("discovery", "")
             for d in all_items["discoveries"]],
            [d.get("session_file", d.get("_session", "")) for d in all_items["discoveries"]],
            "theme",
        )
        patterns.extend(theme_patterns)

        # 2. Recurring topics across ideas
        topic_patterns = self._find_recurring_text(
            [i.get("title", "") + " " + i.get("description", "")
             for i in all_items["ideas"]],
            [i.get("session_file", i.get("_session", "")) for i in all_items["ideas"]],
            "topic",
        )
        patterns.extend(topic_patterns)

        # 3. Recurring error patterns (from best practices that came from solutions)
        error_patterns = self._find_recurring_text(
            [p.get("practice", "") for p in all_items["best_practices"]
             if p.get("auto_detected")],
            [p.get("session_file", p.get("_session", "")) for p in all_items["best_practices"]
             if p.get("auto_detected")],
            "error",
        )
        patterns.extend(error_patterns)

        # 4. Frequent prompt categories
        cat_counts: Counter = Counter()
        cat_sessions: Dict[str, set] = {}
        for p in all_items["prompts"]:
            cat = p.get("category", "general")
            cat_counts[cat] += 1
            cat_sessions.setdefault(cat, set()).add(p.get("session_file", p.get("_session", "")))

        for cat, count in cat_counts.items():
            if count >= 1:
                patterns.append({
                    "pattern_type": "prompt_category",
                    "description": f"Recurring prompt category: {cat} ({count} occurrences)",
                    "frequency": count,
                    "sessions": sorted(s for s in cat_sessions.get(cat, set()) if s),
                })

        # 5. Cross-category: tag-heavy sessions
        session_tag_counts: Dict[str, int] = {}
        for s in sessions:
            count = sum(1 for line in s.lines if any(t in line for t in self.tags.values()))
            if count > 0:
                session_tag_counts[s.name] = count

        high_tag_sessions = sorted(session_tag_counts.items(), key=lambda x: -x[1])
        if len(high_tag_sessions) >= 2:
            patterns.append({
                "pattern_type": "knowledge_density",
                "description": f"Knowledge-dense sessions: "
                               f"{', '.join(f'{n}({c})' for n, c in high_tag_sessions[:5])}",
                "frequency": sum(c for _, c in high_tag_sessions),
                "sessions": [n for n, _ in high_tag_sessions],
            })

        # Sort by frequency descending
        patterns.sort(key=lambda p: p.get("frequency", 0), reverse=True)
        return patterns

    # --- Internal helpers ---

    def _find_recurring_text(self, texts: List[str], sessions: List[str],
                             pattern_type: str) -> List[Dict]:
        """Find recurring meaningful words/phrases across texts."""
        if not texts:
            return []

        # Extract significant words (len > 4, not common stop words)
        stop_words = {"their", "there", "about", "which", "would", "could",
                      "should", "these", "those", "other", "after", "where",
                      "being", "tiene", "puede", "donde", "todos", "estas",
                      "estos", "those", "sobre", "entre", "desde", "hasta"}
        word_sessions: Dict[str, set] = {}
        for text, sess in zip(texts, sessions):
            if not text:
                continue
            words = set(w.lower() for w in re.findall(r"\b\w{5,}\b", text)
                        if w.lower() not in stop_words)
            for w in words:
                word_sessions.setdefault(w, set()).add(sess)

        patterns = []
        for word, sess_set in word_sessions.items():
            if len(sess_set) >= 2:
                patterns.append({
                    "pattern_type": pattern_type,
                    "description": f"Recurring {pattern_type}: '{word}' "
                                   f"appears across {len(sess_set)} session(s)",
                    "frequency": len(sess_set),
                    "sessions": sorted(s for s in sess_set if s),
                })

        # Also check for exact-title repeats
        title_counts: Dict[str, List[str]] = {}
        for text, sess in zip(texts, sessions):
            if not text:
                continue
            key = text[:60].strip().lower()
            if len(key) > 10:
                title_counts.setdefault(key, []).append(sess)

        for title, sess_list in title_counts.items():
            if len(sess_list) >= 2:
                patterns.append({
                    "pattern_type": pattern_type,
                    "description": f"Repeated {pattern_type}: '{title[:80]}'",
                    "frequency": len(sess_list),
                    "sessions": sorted(set(s for s in sess_list if s)),
                })

        return patterns

    def _make_item(self, kind: str, text: str, line_idx: int,
                   auto_detected: bool = True, context: str = "",
                   extra: Optional[Dict] = None) -> Dict:
        """Build a standard knowledge item dict."""
        item = {
            "title": text[:100],
            "extracted_from": line_idx + 1,
            "auto_detected": auto_detected,
            "timestamp": datetime.now().isoformat(),
        }
        if context:
            item["context"] = context
        if kind == "discovery":
            item.update({"discovery": text, "impact": "To be evaluated",
                         "status": "pending_validation"})
        elif kind == "best_practice":
            item.update({"practice": text, "benefit": "To be documented",
                         "status": "pending_validation"})
        if extra:
            item.update(extra)
        return item

    def _parse_tagged_block(self, lines: List[str], idx: int, tag: str,
                            kind: str) -> Optional[Dict]:
        """Parse a tagged line + surrounding context."""
        ctx = " ".join(l.strip() for l in lines[max(0, idx - 3):idx])[:200]
        block = []
        for i in range(idx, min(len(lines), idx + 10)):
            if lines[i].startswith("#") and i > idx:
                break
            block.append(lines[i].strip())
        text = " ".join(block).replace(tag, "").strip()
        m = re.match(r"\*\*(.+?)\*\*[:\s-]*(.*)", text)
        title = m.group(1).strip() if m else (text[:50] + "..." if len(text) > 50 else text)
        discovery = m.group(2).strip() if m else text
        if not text:
            return None
        return self._make_item(kind, discovery, idx, auto_detected=False, context=ctx,
                               extra={"title": title})

    def _parse_list_section(self, lines: List[str], start: int,
                            kind: str) -> List[Dict]:
        """Parse items from a markdown list section."""
        items = []
        buf: List[str] = []
        for i in range(start, len(lines)):
            if lines[i].startswith("## "):
                break
            if lines[i].strip().startswith(("-", "*", "1.", "2.", "3.")):
                if buf:
                    text = re.sub(r"^[-*\d.]+\s*", "", " ".join(l.strip() for l in buf if l.strip()))
                    if text:
                        items.append(self._make_item(kind, text, i, auto_detected=True,
                                                     context="Auto-detected from session"))
                buf = [lines[i]]
            elif buf:
                buf.append(lines[i])
        if buf:
            text = re.sub(r"^[-*\d.]+\s*", "", " ".join(l.strip() for l in buf if l.strip()))
            if text:
                items.append(self._make_item(kind, text, len(lines), auto_detected=True,
                                             context="Auto-detected from session"))
        return items

    def _parse_inline(self, lines: List[str], idx: int, pattern: str,
                      kind: str) -> Optional[Dict]:
        """Parse an inline statement matching a regex pattern."""
        m = re.search(pattern, lines[idx], re.IGNORECASE)
        if m:
            return self._make_item(kind, m.group(1).strip(), idx, auto_detected=True,
                                   context="Auto-detected from inline text")
        return None

    def _code_block_prompt(self, code_lines: List[str], start: int) -> Dict:
        """Create prompt dict from a code block."""
        content = "\n".join(code_lines).strip()
        prompt_id = f"PROMPT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(content) % 10000:04d}"
        return {
            "id": prompt_id,
            "category": self._categorize(content),
            "prompt_template": content,
            "extracted_from": start + 1,
            "status": "validated",
            "auto_detected": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _parse_tagged_prompt(self, lines: List[str], idx: int, tag: str) -> Optional[Dict]:
        """Parse a prompt tagged with #prompt-success."""
        buf = []
        for i in range(max(0, idx - 10), min(len(lines), idx + 5)):
            if lines[i].strip().startswith("```"):
                if i < idx:
                    continue
                else:
                    break
            buf.append(lines[i])
        content = "\n".join(buf).replace(tag, "").strip()
        if not content:
            return None
        prompt_id = f"PROMPT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(content) % 10000:04d}"
        return {
            "id": prompt_id,
            "category": self._categorize(content),
            "prompt_template": content,
            "extracted_from": idx + 1,
            "status": "validated",
            "auto_detected": False,
            "timestamp": datetime.now().isoformat(),
        }

    def _extract_code_solution(self, lines: List[str], idx: int) -> Optional[Dict]:
        """Extract a code solution from surrounding lines."""
        code_start = None
        for i in range(idx - 1, max(0, idx - 20), -1):
            if "```" in lines[i]:
                code_start = i
                break
        if code_start is None:
            return None
        code = []
        for i in range(code_start + 1, idx):
            if "```" in lines[i]:
                break
            code.append(lines[i])
        text = "\n".join(code).strip()
        if not text:
            return None
        return self._make_item("best_practice", text[:500], code_start, auto_detected=True,
                               context=lines[idx].strip(),
                               extra={"title": f"Code solution ({len(code)} lines)",
                                      "benefit": "Successfully resolved an issue",
                                      "status": "validated"})

    @staticmethod
    def _categorize(content: str) -> str:
        """Categorize a prompt by content."""
        cl = content.lower()
        if "python" in cl or "def " in cl or "import " in cl:
            return "python"
        if "bash" in cl or "npm " in cl or "git " in cl:
            return "bash"
        if "javascript" in cl or "function " in cl or "const " in cl:
            return "javascript"
        if "sql" in cl or "select " in cl:
            return "sql"
        if "yaml" in cl or "json" in cl:
            return "config"
        return "general"

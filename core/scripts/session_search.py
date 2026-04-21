#!/usr/bin/env python3
"""
PA Framework — Session Search (Advanced Full-Text Search)
==========================================================
Implementa búsqueda full-text en el índice de sesiones con:
- Búsqueda full-text con ranking BM25-like
- Filtros por fecha, tags, errores, agentes
- API: search_sessions(query, filters, limit)

Usage:
    python core/scripts/session_search.py "query" [--from DATE] [--to DATE] [--topic TOPIC] [--limit N]
    python core/scripts/session_search.py --interactive

Autor: FreakingJSON-PA Framework
Version: 1.0.0 (Phase 5 Workstream 2)
"""

import argparse
import json
import math
import re
from collections import Counter
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


class BM25Search:
    """
    BM25-like full-text search implementation for session search.
    Uses Python stdlib only (no external dependencies).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 searcher.

        Args:
            k1: Term frequency saturation parameter (default 1.5)
            b: Length normalization parameter (default 0.75)
        """
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, str] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.idf_cache: Dict[str, float] = {}
        self.total_docs: int = 0

    def index_documents(self, documents: Dict[str, str]):
        """
        Index a collection of documents.

        Args:
            documents: Dict mapping doc_id to document text
        """
        self.documents = documents
        self.total_docs = len(documents)

        # Calculate document lengths
        self.doc_lengths = {}
        total_length = 0
        for doc_id, text in documents.items():
            tokens = self._tokenize(text)
            length = len(tokens)
            self.doc_lengths[doc_id] = length
            total_length += length

        self.avg_doc_length = total_length / self.total_docs if self.total_docs > 0 else 0

        # Clear IDF cache since documents changed
        self.idf_cache = {}

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words."""
        # Remove punctuation, lowercase, split on whitespace
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Filter short tokens and stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o',
            'en', 'de', 'del', 'al', 'por', 'para', 'con', 'sin', 'sobre',
            'entre', 'desde', 'hasta', 'que', 'cual', 'cuales', 'quien', 'quienes',
            'donde', 'cuando', 'como', 'porque', 'si', 'no', 'lo', 'le', 'les',
            'me', 'te', 'se', 'nos', 'os', 'mi', 'tu', 'su', 'mis', 'tus', 'sus'
        }
        return [t for t in tokens if len(t) > 2 and t not in stopwords]

    def _calculate_idf(self, term: str) -> float:
        """Calculate IDF for a term."""
        if term in self.idf_cache:
            return self.idf_cache[term]

        # Count documents containing the term
        doc_count = 0
        for doc_id, text in self.documents.items():
            tokens = self._tokenize(text)
            if term in tokens:
                doc_count += 1

        # IDF formula: log((N - n + 0.5) / (n + 0.5) + 1)
        if doc_count == 0:
            idf = 0.0
        else:
            idf = math.log((self.total_docs - doc_count + 0.5) / (doc_count + 0.5) + 1)

        self.idf_cache[term] = idf
        return idf

    def _calculate_tf(self, term: str, doc_id: str) -> float:
        """Calculate term frequency for a term in a document."""
        if doc_id not in self.documents:
            return 0.0

        tokens = self._tokenize(self.documents[doc_id])
        term_count = tokens.count(term)
        doc_length = self.doc_lengths.get(doc_id, 0)

        # BM25 TF formula
        if doc_length == 0:
            return 0.0

        tf = term_count * (self.k1 + 1) / (term_count + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length))
        return tf

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for documents matching the query.

        Args:
            query: Search query string
            top_k: Maximum number of results to return

        Returns:
            List of (doc_id, score) tuples sorted by score descending
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores: Dict[str, float] = {}

        for term in query_tokens:
            idf = self._calculate_idf(term)
            if idf == 0:
                continue

            for doc_id in self.documents:
                tf = self._calculate_tf(term, doc_id)
                if doc_id not in scores:
                    scores[doc_id] = 0.0
                scores[doc_id] += idf * tf

        # Sort by score descending
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]


class SessionSearch:
    """
    Advanced session search with filters and ranking.
    """

    def __init__(self):
        self.index_data: Dict = {}
        self.sessions_content: Dict[str, str] = {}
        self.bm25 = BM25Search()
        self._load_index()

    def _load_index(self):
        """Load the sessions index."""
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                    self.index_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARN] Could not load index: {e}")
                self.index_data = {"sessions": []}
        else:
            self.index_data = {"sessions": []}

        # Load session content for full-text search
        self._load_session_content()

        # Index content for BM25
        self.bm25.index_documents(self.sessions_content)

    def _load_session_content(self):
        """Load full content of all sessions."""
        self.sessions_content = {}
        if not SESSIONS_DIR.exists():
            return

        for session_file in SESSIONS_DIR.glob("*.md"):
            if re.match(r"\d{4}-\d{2}-\d{2}", session_file.name):
                try:
                    content = session_file.read_text(encoding='utf-8')
                    self.sessions_content[session_file.stem] = content
                except IOError:
                    pass

    def search_sessions(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search sessions with optional full-text query and filters.

        Args:
            query: Full-text search query (optional)
            filters: Dict with filter criteria:
                - from_date: Start date (YYYY-MM-DD)
                - to_date: End date (YYYY-MM-DD)
                - topic: Topic/tag to filter by
                - session_type: Type of session (features, bugfix, etc.)
                - has_errors: Boolean for sessions with errors
                - min_word_count: Minimum word count
            limit: Maximum number of results

        Returns:
            List of session dicts with scores
        """
        filters = filters or {}
        sessions = self.index_data.get("sessions", [])

        # Apply filters
        filtered_sessions = self._apply_filters(sessions, filters)

        # Apply full-text search if query provided
        if query:
            search_results = self.bm25.search(query, top_k=len(filtered_sessions))
            search_ids = {doc_id: score for doc_id, score in search_results}

            # Filter and score sessions
            scored_sessions = []
            for session in filtered_sessions:
                session_id = session.get("id", "")
                if session_id in search_ids:
                    session_copy = session.copy()
                    session_copy["search_score"] = search_ids[session_id]
                    scored_sessions.append(session_copy)

            # Sort by search score
            scored_sessions.sort(key=lambda x: x.get("search_score", 0), reverse=True)
            return scored_sessions[:limit]
        else:
            # No query, return filtered sessions sorted by date
            filtered_sessions.sort(key=lambda x: x.get("id", ""), reverse=True)
            return filtered_sessions[:limit]

    def _apply_filters(
        self,
        sessions: List[Dict],
        filters: Dict[str, Any]
    ) -> List[Dict]:
        """Apply filter criteria to sessions."""
        result = sessions

        # Date range filter
        from_date = filters.get("from_date")
        if from_date:
            result = [s for s in result if s.get("id", "") >= from_date]

        to_date = filters.get("to_date")
        if to_date:
            result = [s for s in result if s.get("id", "") <= to_date]

        # Topic filter
        topic = filters.get("topic")
        if topic:
            topic_lower = topic.lower()
            result = [
                s for s in result
                if any(topic_lower in t.lower() for t in s.get("topics", []))
            ]

        # Session type filter
        session_type = filters.get("session_type")
        if session_type:
            result = [s for s in result if s.get("type", "") == session_type]

        # Has errors filter
        has_errors = filters.get("has_errors")
        if has_errors is not None:
            if has_errors:
                result = [
                    s for s in result
                    if s.get("stats", {}).get("lsp_errors", 0) > 0
                ]
            else:
                result = [
                    s for s in result
                    if s.get("stats", {}).get("lsp_errors", 0) == 0
                ]

        # Minimum word count filter
        min_word_count = filters.get("min_word_count")
        if min_word_count:
            result = [
                s for s in result
                if s.get("stats", {}).get("word_count", 0) >= min_word_count
            ]

        return result

    def get_search_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on session content."""
        suggestions = set()

        # Look for topics
        for session in self.index_data.get("sessions", []):
            for topic in session.get("topics", []):
                if topic.lower().startswith(prefix.lower()):
                    suggestions.add(topic)

        # Look for common terms in content
        for content in self.sessions_content.values():
            words = re.findall(r'\b\w{4,}\b', content.lower())
            for word in words:
                if word.startswith(prefix.lower()):
                    suggestions.add(word)
                if len(suggestions) >= limit * 2:
                    break

        return sorted(suggestions)[:limit]

    def get_facets(self) -> Dict[str, Any]:
        """Get facet counts for filtering."""
        facets = {
            "topics": Counter(),
            "types": Counter(),
            "date_range": {"min": None, "max": None},
        }

        sessions = self.index_data.get("sessions", [])

        for session in sessions:
            # Topics
            for topic in session.get("topics", []):
                facets["topics"][topic] += 1

            # Types
            session_type = session.get("type", "other")
            facets["types"][session_type] += 1

            # Date range
            session_id = session.get("id", "")
            if session_id:
                if facets["date_range"]["min"] is None or session_id < facets["date_range"]["min"]:
                    facets["date_range"]["min"] = session_id
                if facets["date_range"]["max"] is None or session_id > facets["date_range"]["max"]:
                    facets["date_range"]["max"] = session_id

        return {
            "topics": dict(facets["topics"].most_common(20)),
            "types": dict(facets["types"]),
            "date_range": facets["date_range"],
            "total_sessions": len(sessions),
        }


def format_results(results: List[Dict], verbose: bool = False) -> str:
    """Format search results for display."""
    if not results:
        return "No sessions found."

    output = []
    output.append(f"Found {len(results)} session(s):\n")
    output.append("=" * 70)

    for i, session in enumerate(results, 1):
        session_id = session.get("id", "Unknown")
        title = session.get("title", "Sin título")
        date = session.get("date", session_id)
        topics = ", ".join(session.get("topics", [])) or "Sin tags"
        session_type = session.get("type", "other")
        word_count = session.get("stats", {}).get("word_count", 0)

        output.append(f"\n{i}. [{session_id}] {title}")
        output.append(f"   Type: {session_type} | Topics: {topics}")
        output.append(f"   Words: {word_count}")

        if "search_score" in session:
            output.append(f"   Relevance Score: {session['search_score']:.4f}")

        if verbose:
            summary = session.get("summary", "")
            if summary:
                output.append(f"   Summary: {summary[:150]}...")

    output.append("\n" + "=" * 70)
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="PA Framework Session Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python session_search.py "error handling"
  python session_search.py --topic bugfix --limit 5
  python session_search.py --from 2026-03-01 --to 2026-03-31
  python session_search.py --interactive
        """
    )

    parser.add_argument("query", nargs="?", help="Full-text search query")
    parser.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--topic", help="Filter by topic/tag")
    parser.add_argument("--type", dest="session_type", help="Filter by session type")
    parser.add_argument("--has-errors", action="store_true", help="Show only sessions with errors")
    parser.add_argument("--min-words", type=int, help="Minimum word count")
    parser.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show summaries")
    parser.add_argument("--facets", action="store_true", help="Show facet counts")
    parser.add_argument("--interactive", action="store_true", help="Interactive search mode")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    searcher = SessionSearch()

    # Interactive mode
    if args.interactive:
        print("Session Search - Interactive Mode")
        print("Commands: search <query>, topic <name>, type <name>, facets, quit")
        print("-" * 50)

        while True:
            try:
                user_input = input("\nsearch> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            if user_input.lower() == "facets":
                facets = searcher.get_facets()
                print(f"\nTotal Sessions: {facets['total_sessions']}")
                print(f"Date Range: {facets['date_range']['min']} to {facets['date_range']['max']}")
                print("\nTop Topics:")
                for topic, count in list(facets['topics'].items())[:10]:
                    print(f"  {topic}: {count}")
                print("\nSession Types:")
                for stype, count in facets['types'].items():
                    print(f"  {stype}: {count}")
                continue

            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            query_text = parts[1] if len(parts) > 1 else ""

            if cmd == "search":
                results = searcher.search_sessions(query=query_text, limit=args.limit)
                print(format_results(results, verbose=True))
            elif cmd == "topic":
                results = searcher.search_sessions(filters={"topic": query_text}, limit=args.limit)
                print(format_results(results, verbose=True))
            elif cmd == "type":
                results = searcher.search_sessions(filters={"session_type": query_text}, limit=args.limit)
                print(format_results(results, verbose=True))
            else:
                # Default: search
                results = searcher.search_sessions(query=user_input, limit=args.limit)
                print(format_results(results, verbose=True))

        return

    # Show facets
    if args.facets:
        facets = searcher.get_facets()
        if args.json:
            print(json.dumps(facets, indent=2))
        else:
            print(f"Total Sessions: {facets['total_sessions']}")
            print(f"Date Range: {facets['date_range']['min']} to {facets['date_range']['max']}")
            print("\nTop Topics:")
            for topic, count in list(facets['topics'].items())[:10]:
                print(f"  {topic}: {count}")
            print("\nSession Types:")
            for stype, count in facets['types'].items():
                print(f"  {stype}: {count}")
        return

    # Build filters
    filters = {}
    if args.from_date:
        filters["from_date"] = args.from_date
    if args.to_date:
        filters["to_date"] = args.to_date
    if args.topic:
        filters["topic"] = args.topic
    if args.session_type:
        filters["session_type"] = args.session_type
    if args.has_errors:
        filters["has_errors"] = True
    if args.min_words:
        filters["min_word_count"] = args.min_words

    # Perform search
    results = searcher.search_sessions(
        query=args.query,
        filters=filters,
        limit=args.limit
    )

    # Output results
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_results(results, verbose=args.verbose))


if __name__ == "__main__":
    main()

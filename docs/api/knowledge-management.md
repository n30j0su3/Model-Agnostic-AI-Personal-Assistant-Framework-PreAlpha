# Knowledge Management API Reference

**Modules**: 
- `core/scripts/knowledge-pattern-detector.py` (KnowledgePatternDetector)
- `core/scripts/knowledge-extractor.py` (KnowledgeExtractor)

**Version**: v1.0.0 / v2.0.0  
**Status**: ✅ Frozen (v0.3.8-alpha)  

---

## Overview

The Knowledge Management system provides automated extraction and pattern detection for session knowledge. It identifies discoveries, successful prompts, validated ideas, and best practices from session files.

### Knowledge Types

| Type | Tag | Auto-Detection | Output |
|------|-----|----------------|--------|
| Discoveries | `#discovery` | Section headers, inline patterns | Markdown log |
| Prompts | `#prompt-success` | Code blocks with success indicators | JSON registry |
| Ideas | `#idea` | Validated items with [OK] markers | Markdown log |
| Best Practices | `#best-practice` | Solution sections, working code | Markdown log |

---

## Module: knowledge-pattern-detector.py

Cross-session pattern analysis for recurring themes, topics, and errors.

### Classes

#### SessionContent

Lazy-parsed representation of a session file.

##### Constructor

```python
def __init__(self, path: Path) -> None
```

**Parameters:**
- `path` (Path): Path to session file

##### Properties

- `path` (Path): Original file path
- `name` (str): File name
- `raw` (str): Full file content (lazy-loaded)
- `lines` (List[str]): File content split by lines (lazy-loaded)

##### Methods

###### `invalidate() -> None`

Clear cached content (forces re-read on next access).

---

#### PatternDetector

Detects knowledge patterns within and across sessions.

##### Constructor

```python
def __init__(
    self,
    tags: Optional[Dict[str, str]] = None,
    auto_detect: Optional[Dict[str, bool]] = None
) -> None
```

**Parameters:**
- `tags` (Optional[Dict[str, str]]): Custom tag mappings
- `auto_detect` (Optional[Dict[str, bool]]): Enable/disable auto-detection per type

**Default Tags:**
```python
{
    "discovery": "#discovery",
    "prompt_success": "#prompt-success",
    "idea": "#idea",
    "best_practice": "#best-practice",
}
```

**Default Auto-Detect:**
```python
{
    "discoveries": True,
    "prompts": True,
    "ideas": True,
    "best_practices": True,
}
```

---

##### Single-Session Extraction Methods

###### `extract_discoveries(session: SessionContent) -> List[Dict]`

Extract discoveries from a single session.

**Parameters:**
- `session` (SessionContent): Session to analyze

**Returns:**
- `List[Dict]`: List of discovery items with keys:
  - `title` (str): Discovery title
  - `discovery` (str): Discovery description
  - `extracted_from` (int): Line number
  - `auto_detected` (bool): Whether auto-detected or tag-based
  - `session_file` (str): Source file name
  - `context` (str): Surrounding context
  - `impact` (str): Impact assessment (pending validation)
  - `status` (str): "pending_validation"

**Example:**
```python
from knowledge_pattern_detector import PatternDetector, SessionContent

detector = PatternDetector()
session = SessionContent(Path("session-20260417.md"))
discoveries = detector.extract_discoveries(session)

for d in discoveries:
    print(f"{d['title']}: {d['discovery']}")
```

---

###### `extract_prompts(session: SessionContent) -> List[Dict]`

Extract successful prompts from a single session.

**Parameters:**
- `session` (SessionContent): Session to analyze

**Returns:**
- `List[Dict]`: List of prompt items with keys:
  - `id` (str): Unique prompt ID
  - `category` (str): Prompt category
  - `prompt_template` (str): The prompt content
  - `extracted_from` (int): Line number
  - `status` (str): "validated"
  - `auto_detected` (bool): Detection method
  - `timestamp` (str): ISO timestamp

**Example:**
```python
prompts = detector.extract_prompts(session)
for p in prompts:
    print(f"{p['id']}: {p['category']} - {p['prompt_template'][:50]}...")
```

---

###### `extract_ideas(session: SessionContent) -> List[Dict]`

Extract validated ideas from a single session.

**Parameters:**
- `session` (SessionContent): Session to analyze

**Returns:**
- `List[Dict]`: List of idea items with keys:
  - `title` (str): Idea title
  - `description` (str): Idea description
  - `extracted_from` (int): Line number
  - `auto_detected` (bool): Detection method
  - `priority` (str): "high", "medium", or "low"
  - `status` (str): "validated" or "pending"
  - `session_file` (str): Source file name

---

###### `extract_best_practices(session: SessionContent) -> List[Dict]`

Extract best practices from a single session.

**Parameters:**
- `session` (SessionContent): Session to analyze

**Returns:**
- `List[Dict]`: List of best practice items with keys:
  - `title` (str): Practice title
  - `practice` (str): Practice description
  - `extracted_from` (int): Line number
  - `auto_detected` (bool): Detection method
  - `context` (str): Surrounding context
  - `benefit` (str): Documented benefit
  - `status` (str): "pending_validation" or "validated"

---

##### Cross-Session Analysis

###### `analyze_sessions(session_paths: List[Path]) -> List[Dict]`

Cross-session pattern analysis.

**Parameters:**
- `session_paths` (List[Path]): List of session file paths to analyze

**Returns:**
- `List[Dict]`: List of Pattern dicts with keys:
  - `pattern_type` (str): One of "theme", "topic", "error", "discovery", "practice", "prompt_category", "knowledge_density"
  - `description` (str): Human-readable pattern description
  - `frequency` (int): Number of occurrences
  - `sessions` (List[str]): Session file names where pattern appears

**Example:**
```python
from pathlib import Path

sessions_dir = Path("core/.context/sessions")
session_files = list(sessions_dir.glob("*.md"))[-10:]  # Last 10 sessions

patterns = detector.analyze_sessions(session_files)

for p in patterns:
    print(f"[{p['pattern_type']}] {p['description']}")
    print(f"  Frequency: {p['frequency']} sessions: {', '.join(p['sessions'][:3])}")
```

**Pattern Types:**

1. **theme**: Recurring themes from discoveries
2. **topic**: Recurring topics across ideas
3. **error**: Recurring error patterns from solutions
4. **prompt_category**: Frequent prompt categories
5. **knowledge_density**: Sessions with high knowledge tag density

---

### Decorators

#### `lazy_load(attr_name: str)`

Decorator that defers file reading until first access.

**Parameters:**
- `attr_name` (str): Attribute name to cache

**Example:**
```python
class MySession:
    @lazy_load("content")
    def load_content(self) -> str:
        return self.path.read_text()
```

---

## Module: knowledge-extractor.py

Dual output system (JSON + MD) for knowledge extraction from sessions.

### Class: KnowledgeExtractor

Orchestrates knowledge extraction and file output.

#### Constructor

```python
def __init__(self, config: Optional[Dict] = None) -> None
```

**Parameters:**
- `config` (Optional[Dict]): Configuration overrides

**Default Configuration:**
```python
{
    "enabled": True,
    "auto_detect": {
        "discoveries": True,
        "prompts": True,
        "ideas": True,
        "best_practices": True,
    },
    "tags": {
        "discovery": "#discovery",
        "prompt_success": "#prompt-success",
        "idea": "#idea",
        "best_practice": "#best-practice",
    },
    "output": {
        "discoveries": "core/.context/knowledge/learning/discoveries.md",
        "prompts": "core/.context/knowledge/prompts/registry.json",
        "ideas": "core/.context/codebase/ideas.md",
        "best_practices": "core/.context/knowledge/learning/best-practices.md",
        "index": "core/.context/knowledge/knowledge-index.json",
    },
}
```

---

#### Properties

- `discoveries_file` (Path): Path to discoveries markdown file
- `prompts_file` (Path): Path to prompts JSON registry
- `ideas_file` (Path): Path to ideas markdown file
- `best_practices_file` (Path): Path to best practices markdown file
- `index_file` (Path): Path to knowledge index JSON

---

#### Extraction Methods

###### `extract_session_discoveries(session_file: Path) -> List[Dict]`

Extract discoveries from a session file.

**Parameters:**
- `session_file` (Path): Path to session file

**Returns:**
- `List[Dict]`: List of discovery items

---

###### `extract_successful_prompts(session_file: Path) -> List[Dict]`

Extract successful prompts from a session file.

**Parameters:**
- `session_file` (Path): Path to session file

**Returns:**
- `List[Dict]`: List of prompt items

---

###### `extract_validated_ideas(session_file: Path) -> List[Dict]`

Extract validated ideas from a session file.

**Parameters:**
- `session_file` (Path): Path to session file

**Returns:**
- `List[Dict]`: List of idea items

---

###### `extract_best_practices(session_file: Path) -> List[Dict]`

Extract best practices from a session file.

**Parameters:**
- `session_file` (Path): Path to session file

**Returns:**
- `List[Dict]`: List of best practice items

---

###### `extract_all_knowledge(session_file: Path) -> Dict`

Extract all knowledge types from a session and update output files.

**Parameters:**
- `session_file` (Path): Path to session file

**Returns:**
- `Dict` with keys:
  - `discoveries` (int): Count of discoveries extracted
  - `prompts` (int): Count of prompts extracted
  - `ideas` (int): Count of ideas extracted
  - `best_practices` (int): Count of best practices extracted
  - `success` (bool): Whether all updates succeeded
  - `session_file` (str): Source file name
  - `message` (str, optional): Error message if failed

**Example:**
```python
from knowledge_extractor import KnowledgeExtractor

extractor = KnowledgeExtractor()
results = extractor.extract_all_knowledge(Path("session-20260417.md"))

print(f"Extracted: {results['discoveries']} discoveries, "
      f"{results['prompts']} prompts, {results['ideas']} ideas, "
      f"{results['best_practices']} practices")
```

---

#### File Update Methods

###### `update_discoveries_file(discoveries: List[Dict]) -> bool`

Append discoveries to the discoveries markdown file.

**Parameters:**
- `discoveries` (List[Dict]): List of discovery items

**Returns:**
- `bool`: True if successful

---

###### `update_prompts_registry(prompts: List[Dict]) -> bool`

Update the prompts JSON registry (deduplicates by ID).

**Parameters:**
- `prompts` (List[Dict]): List of prompt items

**Returns:**
- `bool`: True if successful

---

###### `update_ideas_file(ideas: List[Dict]) -> bool`

Append ideas to the ideas markdown file.

**Parameters:**
- `ideas` (List[Dict]): List of idea items

**Returns:**
- `bool`: True if successful

---

###### `update_best_practices_file(practices: List[Dict]) -> bool`

Append best practices to the best practices markdown file.

**Parameters:**
- `practices` (List[Dict]): List of best practice items

**Returns:**
- `bool`: True if successful

---

###### `update_knowledge_index(stats: Dict) -> bool`

Update the knowledge index with extraction statistics.

**Parameters:**
- `stats` (Dict): Statistics dict with counts

**Returns:**
- `bool`: True if successful

---

### Convenience Functions

Module-level functions for quick access without instantiation:

```python
from knowledge_extractor import (
    extract_all_knowledge,
    extract_session_discoveries,
    extract_successful_prompts,
    extract_validated_ideas,
    extract_best_practices,
)

# Quick extraction
results = extract_all_knowledge(Path("session.md"))

# Individual extraction
discoveries = extract_session_discoveries(Path("session.md"))
prompts = extract_successful_prompts(Path("session.md"))
```

---

## Usage Examples

### Basic Knowledge Extraction

```python
from pathlib import Path
from knowledge_extractor import KnowledgeExtractor

# Initialize extractor
extractor = KnowledgeExtractor()

# Extract from session
session_file = Path("core/.context/sessions/session-20260417.md")
results = extractor.extract_all_knowledge(session_file)

print(f"Success: {results['success']}")
print(f"Extracted {results['discoveries'] + results['ideas'] + results['best_practices']} knowledge items")
```

### Pattern Analysis Across Sessions

```python
from pathlib import Path
from knowledge_pattern_detector import PatternDetector

detector = PatternDetector()

# Get recent sessions
sessions_dir = Path("core/.context/sessions")
recent_sessions = sorted(
    sessions_dir.glob("*.md"),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)[:10]

# Analyze patterns
patterns = detector.analyze_sessions(recent_sessions)

# Display top patterns
print("=== Top Knowledge Patterns ===")
for i, pattern in enumerate(patterns[:5], 1):
    print(f"\n{i}. [{pattern['pattern_type']}]")
    print(f"   {pattern['description']}")
    print(f"   Frequency: {pattern['frequency']} sessions")
```

### Custom Configuration

```python
from knowledge_extractor import KnowledgeExtractor

custom_config = {
    "enabled": True,
    "auto_detect": {
        "discoveries": True,
        "prompts": False,  # Disable prompt auto-detection
        "ideas": True,
        "best_practices": True,
    },
    "tags": {
        "discovery": "#discovery",
        "prompt_success": "#prompt-success",
        "idea": "#idea",
        "best_practice": "#best-practice",
    },
    "output": {
        "discoveries": "custom/output/discoveries.md",
        "prompts": "custom/output/prompts.json",
        "ideas": "custom/output/ideas.md",
        "best_practices": "custom/output/practices.md",
        "index": "custom/output/index.json",
    },
}

extractor = KnowledgeExtractor(config=custom_config)
```

### Session-End Pipeline Integration

```python
from pathlib import Path
from knowledge_extractor import KnowledgeExtractor
from knowledge_pattern_detector import PatternDetector

def session_end_pipeline(session_file: Path):
    """Run knowledge extraction as part of session end."""
    
    # Step 1: Extract knowledge from this session
    extractor = KnowledgeExtractor()
    results = extractor.extract_all_knowledge(session_file)
    
    if not results['success']:
        print("Warning: Knowledge extraction had errors")
    
    # Step 2: Analyze patterns across recent sessions
    sessions_dir = session_file.parent
    recent_sessions = sorted(
        sessions_dir.glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )[:20]
    
    detector = PatternDetector()
    patterns = detector.analyze_sessions(recent_sessions)
    
    # Step 3: Report findings
    print(f"\n=== Knowledge Extraction Summary ===")
    print(f"Session: {session_file.name}")
    print(f"Discoveries: {results['discoveries']}")
    print(f"Prompts: {results['prompts']}")
    print(f"Ideas: {results['ideas']}")
    print(f"Best Practices: {results['best_practices']}")
    
    if patterns:
        print(f"\n=== Top Patterns Detected ===")
        for p in patterns[:3]:
            print(f"- {p['description']}")
    
    return results, patterns
```

---

## Output Formats

### Discoveries Markdown Format

```markdown
### 2026-04-17: [PENDIENTE VALIDACION] Discovery Title

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/session-20260417.md#L42
> **Deteccion**: automatica

**Contexto**: Surrounding context...

**Descubrimiento**: Full discovery description...

**Impacto**: To be evaluated

---
```

### Prompts JSON Registry Format

```json
{
  "prompts": [
    {
      "id": "PROMPT-20260417123456-0001",
      "category": "code_generation",
      "prompt_template": "Write a Python function that...",
      "extracted_from": 42,
      "status": "validated",
      "auto_detected": true,
      "timestamp": "2026-04-17T12:34:56",
      "session_file": "session-20260417.md"
    }
  ],
  "last_updated": "2026-04-17T12:34:56"
}
```

### Knowledge Index Format

```json
{
  "discoveries": 150,
  "prompts": 45,
  "ideas": 78,
  "best_practices": 32,
  "last_extraction": "2026-04-17T12:34:56",
  "history": [
    {
      "timestamp": "2026-04-17T12:34:56",
      "session": "session-20260417.md",
      "discoveries": 3,
      "prompts": 1,
      "ideas": 2,
      "best_practices": 1
    }
  ]
}
```

---

## Testing

### Unit Test Example

```python
import pytest
from pathlib import Path
from knowledge_pattern_detector import PatternDetector, SessionContent
from knowledge_extractor import KnowledgeExtractor

def test_extract_discoveries():
    detector = PatternDetector()
    session = SessionContent(Path("test_session.md"))
    discoveries = detector.extract_discoveries(session)
    assert isinstance(discoveries, list)

def test_extract_all_knowledge():
    extractor = KnowledgeExtractor()
    results = extractor.extract_all_knowledge(Path("test_session.md"))
    assert "discoveries" in results
    assert "prompts" in results
    assert "success" in results

def test_analyze_sessions():
    detector = PatternDetector()
    patterns = detector.analyze_sessions([Path("session1.md"), Path("session2.md")])
    assert isinstance(patterns, list)
```

---

## Performance Considerations

### Lazy Loading

SessionContent uses lazy loading for file content. Large session files are only read when accessed.

### Caching

PatternDetector does not cache by default. For repeated analysis of the same sessions, implement external caching.

### Batch Processing

For processing many sessions, use batch operations:

```python
# Efficient batch processing
sessions = list(sessions_dir.glob("*.md"))
all_patterns = detector.analyze_sessions(sessions)
```

---

## Related Documentation

- [ContextLoader API](context-loader.md) — Context loading system
- [Recovery System API](recovery-system.md) — Error recovery orchestration
- [ErrorLogger API](knowledge-management.md) — Error logging (integrated)

---

*Last updated: April 17, 2026*  
*Phase 5 Workstream 1 — API Stabilization*

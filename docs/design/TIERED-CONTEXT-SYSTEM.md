---
version: "0.2.2"
status: design
created: 2026-04-16
author: PA Framework Team
target_phase: 2
---

# Tiered Context System - Design Document

> **PA Framework v0.2.2 — Phase 2 Core Architecture**

---

## 🎯 Overview

The Tiered Context System is a hierarchical storage architecture designed to optimize context loading, reduce memory footprint, and preserve session data across model instances.

### Goals

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Active context size | ~5KB | <1KB | -80% |
| Session load time | ~2s | <500ms | -75% |
| Storage footprint | Monolithic MD | JSONL compressed | -50% |
| Preservation rate | ~60% | >80% | +33% |

---

## 🏗️ Architecture

### Three-Tier System

```
┌─────────────────────────────────────────────────────────────┐
│                     HOT TIER (Active)                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • Active session only                                    ││
│  │ • In-memory dict                                         ││
│  │ • <1KB target size                                       ││
│  │ • TTL: Duration of session                               ││
│  │ • Format: Python dict + JSONL append                     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              │ session-end.py / demotion
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    WARM TIER (Recent)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • Last 7 days of sessions                                ││
│  │ • JSONL storage (append-only)                            ││
│  │ • Stream-friendly access                                 ││
│  │ • TTL: 7 days → then cold                                ││
│  │ • Format: .jsonl files per day                           ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              │ archive / 7+ days old
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    COLD TIER (Archive)                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • Sessions older than 7 days                             ││
│  │ • Compressed .jsonl.gz files                             ││
│  │ • Monthly archive bundles                                ││
│  │ • On-demand decompression                                ││
│  │ • TTL: Infinite (manual cleanup)                         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
core/.context/
├── sessions/                    # HOT tier (current session)
│   ├── current.json           # Active session state (<1KB)
│   ├── .events/               # Event stream (JSONL)
│   │   └── YYYY-MM-DD.jsonl   # Daily event files
│   └── archive/               # WARM tier
│       ├── 2026-04/           # Monthly folders
│       │   ├── 2026-04-01.jsonl
│       │   ├── 2026-04-02.jsonl
│       │   └── ...
│       └── cold/              # COLD tier
│           ├── 2026-03.jsonl.gz
│           └── 2026-02.jsonl.gz
├── knowledge/
│   └── sessions-index.json    # Metadata index
└── tiered-config.yaml         # Tier configuration
```

---

## 📊 JSONL Format Specification

### Event Record Schema

```json
{
  "id": "evt-a1b2c3d4",
  "type": "message|action|error|session_start|session_end",
  "timestamp": "2026-04-16T13:06:18.556907Z",
  "source": "cli-instance-id",
  "data": {
    "role": "user|assistant",
    "content": "...",
    "metadata": {}
  },
  "tier": "hot",
  "preserved": true
}
```

### Session Record Schema

```json
{
  "id": "session-2026-04-16",
  "date": "2026-04-16",
  "agent": "FreakingJSON",
  "status": "active|completed|interrupted",
  "time_start": "13:06",
  "time_end": "14:30",
  "events_count": 42,
  "topics": ["phase2", "tiered-context"],
  "summary": "Completed Phase 2 design...",
  "preservation_score": 0.95
}
```

---

## 🔄 Tier Transitions

### Hot → Warm (Session End)

```python
def promote_to_warm(session_id: str):
    """
    Called by session-end.py
    1. Append final session state to daily JSONL
    2. Compress in-memory context
    3. Clear hot tier
    4. Update sessions-index.json
    """
    pass
```

### Warm → Cold (7+ days)

```python
def archive_to_cold(older_than_days: int = 7):
    """
    Called by cron job or manual trigger
    1. Find sessions older than threshold
    2. Compress to .jsonl.gz
    3. Move to cold/ directory
    4. Update index
    """
    pass
```

### Cold → Warm (Retrieval)

```python
def retrieve_from_cold(session_id: str):
    """
    On-demand retrieval
    1. Decompress relevant archive
    2. Load into warm tier temporarily
    3. Return requested data
    """
    pass
```

---

## 📐 Size Estimations

| Tier | Typical Size | Max Size | Format |
|------|-------------|----------|--------|
| Hot | <1KB | 5KB | Python dict (memory) |
| Warm | ~10KB/day | 100KB/day | JSONL (disk) |
| Cold | ~2KB/day | N/A | JSONL.gz (disk) |

### Calculation

- **Hot**: Active session context only (~500 bytes avg)
- **Warm**: 7 days × 10KB = 70KB max
- **Cold**: 30 days × 2KB = 60KB/month compressed

---

## 🔧 Implementation Components

### 1. TieredStorageManager

```python
# core/scripts/tiered_storage.py

class TieredStorageManager:
    """
    Manages Hot/Warm/Cold tier transitions.
    Model-agnostic, no external dependencies.
    """
    
    TIERS = ['hot', 'warm', 'cold']
    
    def __init__(self, context_dir: Path):
        self.context_dir = context_dir
        self.hot_file = context_dir / "sessions" / "current.json"
        self.warm_dir = context_dir / "sessions" / "archive"
        self.cold_dir = context_dir / "sessions" / "archive" / "cold"
        self.config = self._load_config()
    
    # Hot tier operations
    def get_hot(self) -> dict: ...
    def set_hot(self, data: dict): ...
    def clear_hot(self): ...
    
    # Warm tier operations
    def append_warm(self, event: dict): ...
    def get_warm(self, date: str) -> list: ...
    def get_warm_range(self, start: str, end: str) -> list: ...
    
    # Cold tier operations
    def archive_to_cold(self, older_than_days: int = 7): ...
    def retrieve_from_cold(self, session_id: str) -> dict: ...
    
    # Tier transitions
    def promote_to_warm(self): ...
    def demote_to_cold(self): ...
```

### 2. JSONLWriter

```python
class JSONLWriter:
    """Append-only writer for JSONL files."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self._ensure_parent()
    
    def append(self, record: dict):
        """Append a single record to JSONL file."""
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    def append_batch(self, records: list):
        """Append multiple records efficiently."""
        with open(self.filepath, 'a', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
```

### 3. JSONLReader

```python
class JSONLReader:
    """Stream-friendly reader for JSONL files."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
    
    def read_all(self) -> list:
        """Read all records into memory."""
        records = []
        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                records.append(json.loads(line.strip()))
        return records
    
    def stream(self) -> Iterator[dict]:
        """Stream records one at a time."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                yield json.loads(line.strip())
    
    def find_by_id(self, id: str) -> Optional[dict]:
        """Find a record by ID without loading all."""
        for record in self.stream():
            if record.get('id') == id:
                return record
        return None
```

---

## 🔄 Integration Points

### session-start.py

```python
# Initialize tiered storage
storage = TieredStorageManager(CONTEXT_DIR)

# Load hot tier (current session)
current_session = storage.get_hot()
if not current_session:
    current_session = storage.create_new_session()

# Check for pending promotions
storage.check_pending_transitions()
```

### session-end.py

```python
# Promote to warm tier
storage.promote_to_warm()

# Archive old sessions to cold
storage.archive_to_cold(older_than_days=7)

# Update sessions index
storage.update_index()
```

### knowledge-miner.py

```python
# Stream from warm tier for knowledge extraction
for event in JSONLReader(warm_file).stream():
    if event['type'] == 'message':
        extract_knowledge(event)
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
def test_hot_tier_roundtrip():
    storage = TieredStorageManager(tmp_path)
    storage.set_hot({'test': 'data'})
    assert storage.get_hot() == {'test': 'data'}

def test_warm_append():
    storage = TieredStorageManager(tmp_path)
    storage.append_warm({'id': '1', 'type': 'test'})
    events = storage.get_warm(date.today())
    assert len(events) == 1

def test_cold_archive():
    storage = TieredStorageManager(tmp_path)
    storage.archive_to_cold(older_than_days=0)
    assert cold_dir.exists()
```

### Integration Tests

```python
def test_session_preservation_rate():
    """Test that >80% of session data is preserved across tiers."""
    # Create test session with 100 events
    # Run session-end
    # Verify events in warm tier
    # Run archive
    # Verify retrieval from cold tier
    pass
```

---

## 📋 Migration Plan

### Phase 1: Preparation (Day 1)

1. Create `TieredStorageManager` class
2. Create `JSONLWriter` and `JSONLReader` classes
3. Create `tiered-config.yaml`

### Phase 2: Parallel Run (Day 2-3)

1. Dual-write: both old MD and new JSONL
2. Verify data consistency
3. Performance benchmarks

### Phase 3: Cutover (Day 4)

1. Switch to JSONL as primary
2. Keep MD as backup for 7 days
3. Add migration script for old sessions

### Phase 4: Cleanup (Day 5+)

1. Remove dual-write code
2. Archive old MD files to cold tier
3. Update documentation

---

## 📊 Metrics

### Key Performance Indicators

```yaml
metrics:
  hot_tier_size:
    target: <1024  # bytes
    current: null
  
  warm_tier_load_time:
    target: <500  # ms
    current: null
  
  cold_tier_decompress_time:
    target: <2000  # ms
    current: null
  
  preservation_rate:
    target: >80  # percent
    current: 60
  
  storage_reduction:
    target: >50  # percent vs MD
    current: null
```

---

## 🔐 Safety Guarantees

1. **Atomic writes**: Use temp file + rename for JSONL appends
2. **Backup before migration**: Keep original MD files until verified
3. **Corruption recovery**: JSONL line-based format allows partial recovery
4. **Index integrity**: sessions-index.json updated atomically

---

## 🚀 Next Steps

1. ✅ Design document complete
2. ⏳ Implement `TieredStorageManager`
3. ⏳ Implement `JSONLWriter` / `JSONLReader`
4. ⏳ Update `session-start.py` integration
5. ⏳ Update `session-end.py` integration
6. ⏳ Create preservation test script
7. ⏳ Create 7 new playbooks (PB-009 to PB-015)

---

*End of Design Document v0.2.2*
# AGENTS — Framework Bootstrap (Tier 0)

> **Version: v0.4.1-beta** | **Industry Standard Entry Point**
> **Phase 3 Prototype**: Context Loader + Recovery Orchestrator + Modular Knowledge Extraction

---

## 🚀 INITIALIZATION TRIGGER

```bash
python core/scripts/session_start.py
```

**Canonical bootstrap**: `AGENTS-lite.md` is Tier 0 consumed by `ContextLoader`. This file (`AGENTS.md`) is Tier 1 router/operations. `session_start.py` loads Tier 0-1 immediately and defers Tier 2-4 lazily.

**Fallback files** (if script unavailable):
1. `core/.context/MASTER.md` → Global config
2. `core/agents/pa-assistant.md` → Main agent
3. `core/skills/SKILLS.md` → Skills catalog

---

## 📋 AGENT ROUTER

| Agent | Purpose | File |
|-------|---------|------|
| **@FreakingJSON-PA** | Main orchestrator | `core/agents/pa-assistant.md` |
| **@context-scout** | Context discovery | `core/agents/subagents/context-scout.md` |
| **@skill-finder** | Skill routing | `core/agents/subagents/skill-finder.md` |
| **@session-manager** | Session handling | `core/agents/subagents/session-manager.md` |
| **@doc-writer** | MVI documentation | `core/agents/subagents/doc-writer.md` |

---

## ✅ VERSION CHECK

```bash
cat VERSION → Current version
python core/scripts/version_updater.py → Sync versions
```

**Critical files must match**: `VERSION`, `README.md`, `AGENTS.md`, `config/branding.txt`

---

## 📚 REFERENCE TIERS

| Tier | File | Content |
|------|------|---------|
| **Tier 0** | `AGENTS-lite.md` | Bootstrap mínimo (<500 tokens) |
| **Tier 1** | `AGENTS.md` | Router operativo |
| **Tier 2** | `core/.context/MASTER.md` | User config & preferences |
| **Tier 3** | `core/agents/pa-assistant.md` | Agent workflow |
| **Tier 4** | `AGENTS-full.md` | Complete documentation |

### Phase 3 modules

- `core/scripts/context_loader.py` — Tiered context bootstrap
- `core/recovery/orchestrator.py` + `core/recovery/triggers.py` — Recovery orchestration
- `core/scripts/error_logger.py` — Error Logger v2
- `core/scripts/knowledge_extractor.py` + `core/scripts/knowledge_pattern_detector.py` — Modular knowledge extraction

---

## 🧠 PERSISTENT MEMORY WORKFLOW (ADAPTIVE)

- Fuente primaria: `core/.context/sessions/YYYY-MM-DD.md`
- Routing no estático por evento:
  - `.md` = universal
  - `SQLite` = consultas
  - `Memory MD` = conocimiento reutilizable
  - `Wiki` = documentación formal
- Referencia: `docs/MEMORY-ARCHITECTURE.md`

---

## 🔚 SESSION END

```bash
python core/scripts/session_end.py
```

---

## 📖 EXTENDED DOCUMENTATION

- **Full docs**: `AGENTS-full.md` — Complete initialization protocol, CORE processes, enforcement system
- **Quick menu**: `python core/scripts/pa.py` — Interactive menu (el equipo spec)

---

*Agents: This is the industry-standard entry point. Load this file first.*
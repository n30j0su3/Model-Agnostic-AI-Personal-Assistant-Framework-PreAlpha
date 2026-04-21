# Windows Cross-Platform Validation Checklist

**Priority**: Windows > macOS > Linux
**Target Users**: End-users likely on Windows/Mac

---

## Core Files Validation

### ✅ session_memory.py
- Uses `Path(__file__).parent.parent` for framework root
- `PA_FRAMEWORK_DATA` env override supported
- Creates `data/` relative to framework directory
- **STATUS**: PASS — Cross-platform ready

### ✅ cron_setup.py
- Added `import tempfile` (line 31)
- Uses `tempfile.gettempdir()` for log paths
- Replaced hardcoded `/tmp` with `os.path.join(temp_dir, ...)`
- **STATUS**: PASS — Fixed in commit 788f708

### ✅ phase4_metrics_test.py
- Test paths use `tempfile.gettempdir()`
- **STATUS**: PASS — Fixed in commit 788f708

---

## Windows-Specific Checks

### Paths
| Check | Status | Notes |
|-------|--------|-------|
| No `/tmp` hardcoded | ✅ | All use `tempfile.gettempdir()` |
| No `/home` hardcoded | ✅ | session_memory uses `Path(__file__)` |
| No `~/.local` or `~/.config` | ✅ | Data stored in framework `data/` |
| Uses `os.path.join` or `Path` | ✅ | All path construction uses Path/os.path |

### Python Compatibility
| Check | Status | Notes |
|-------|--------|-------|
| Python 3.8+ compatible | ✅ | No Python 3.10+ only features |
| No Unix-only imports | ✅ | No `fcntl`, `syslog`, etc. |
| subprocess calls cross-platform | ✅ | Uses `subprocess.run()` |
| SQLite works on Windows | ✅ | sqlite3 is standard library |

### File Operations
| Check | Status | Notes |
|-------|--------|-------|
| `Path.write_text()` | ✅ | Cross-platform |
| `Path.read_text()` | ✅ | Cross-platform |
| `Path.mkdir(parents=True, exist_ok=True)` | ✅ | Cross-platform |
| No `chmod` Unix-specific calls | ⚠️ | NEEDS REVIEW |

---

## Pending Checks

### ⚠️ message_hook.py
- Verify shell hook paths work on Windows
- Check for Unix-only shell assumptions
- Test with PowerShell vs bash

### ⚠️ Windows Task Scheduler
- `cron_setup.py` Windows implementation (class `_WindowsCronSetup`)
- Verify XML generation for Task Scheduler
- Test `schtasks` command execution

### ⚠️ macOS launchd
- plist generation tested on Linux only
- `launchctl` commands need macOS testing

---

## Test Plan

### Phase 1: Architecture Validation ✅
- [x] No hardcoded Unix paths
- [x] SQLite storage cross-platform
- [x] Temp files use `tempfile.gettempdir()`
- [x] Framework-relative data storage

### Phase 2: Windows Testing (PENDING)
- [ ] Run on Windows machine
- [ ] Test `session-start.py` initialization
- [ ] Test `session_memory.py` SQLite operations
- [ ] Test `cron_setup.py --setup` on Windows
- [ ] Verify temp directory correct (AppData/Local/Temp)

### Phase 3: macOS Testing (PENDING)
- [ ] Run on macOS machine
- [ ] Test launchd plist generation
- [ ] Verify `launchctl` commands work
- [ ] Test Homebrew Python paths

---

## CLI Integration (Windows)

Target CLIs must work on Windows:
| CLI | Windows Support | Notes |
|-----|-----------------|-------|
| OpenCode | ✅ | Windows binary available |
| Claude Code | ✅ | Node.js based, works on Windows |
| Gemini CLI | ✅ | Python, cross-platform |
| Qwen Code | ✅ | Python, cross-platform |
| Codex | ✅ | OpenAI CLI works on Windows |

Shell hooks need PowerShell equivalent:
```powershell
# PowerShell equivalent for bash hook
$env:PA_HOOK_OUTPUT = "C:\path\to\framework\data\hooks\output.json"
```

---

## Recommendations

1. **Test on real Windows machine** — VM or physical
2. **Add Windows CI** — GitHub Actions with `windows-latest`
3. **Create PowerShell hook script** — `message_hook.ps1`
4. **Document Windows setup** — Add to README

---

**Last Updated**: 2026-04-18 (commit 788f708)
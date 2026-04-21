# Release Validation Checklist

> **Version**: 0.3.7-alpha
> **Generated**: 2026-04-20 18:40:02
> **Status**: PENDING VALIDATION

---

## Security Checks

- [ ] No credentials/tokens in any file
- [ ] No internal PRPs in root
- [ ] No .opencode/plans/ in root
- [ ] No test_*.py scripts
- [ ] No internal docs (backlog, AGENT-CONFIGURATION, etc.)
- [ ] README.md is user-facing

**Verify**:
```bash
grep -rE "token|password|secret|api_key|pk_|sk_" . --include="*.py" --include="*.json" --include="*.yaml" 2>/dev/null || echo "OK"
ls PRPs/ 2>/dev/null || echo "OK: No PRPs"
```

---

## Functionality Checks

- [ ] `python core/scripts/session_start.py` runs
- [ ] All core skills present in `core/skills/core/`

---

## Documentation Checks

- [ ] VERSION = CHANGELOG.md entry
- [ ] AGENTS.md has correct version
- [ ] README.md user-friendly

---

## Ready for Push

- [ ] All checks passed
- [ ] User reviewed staging

---

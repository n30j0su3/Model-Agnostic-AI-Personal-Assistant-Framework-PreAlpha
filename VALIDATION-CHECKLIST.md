# Release Validation Checklist / Checklist de Validación de Release

> **Version**: 0.2.0-prealpha
> **Generated**: 2026-03-12 13:47:56
> **Status**: PENDING VALIDATION

---

## Security Checks / Verificaciones de Seguridad

- [ ] No credentials/tokens in any file
- [ ] No internal PRPs in root (should be in Obsoleto/)
- [ ] No .opencode/plans/ in root
- [ ] No test_*.py scripts
- [ ] No internal docs (backlog, AGENT-CONFIGURATION, etc.)
- [ ] README.md is user-facing (not technical)

**Verify with**:
```bash
grep -r "token|password|secret|api_key" . --include="*.py" --include="*.json" --include="*.yaml"
ls PRPs/ 2>/dev/null || echo "OK: No PRPs in root"
```

---

## Functionality Checks / Verificaciones de Funcionalidad

- [ ] `python core/scripts/session-start.py` runs without errors
- [ ] `python core/scripts/session-end.py --summary` shows correct version
- [ ] `dashboard.html` opens correctly in browser
- [ ] All core skills are present in `core/skills/core/`

**Quick test**:
```bash
python core/scripts/session-start.py
python core/scripts/version-updater.py --dry-run
```

---

## Documentation Checks / Verificaciones de Documentación

- [ ] VERSION file matches CHANGELOG.md
- [ ] README.md has correct version badge
- [ ] AGENTS.md has correct version
- [ ] CHANGELOG.md has entry for this version

---

## Ready for Push / Listo para Push

- [ ] All security checks passed
- [ ] All functionality checks passed
- [ ] All documentation checks passed
- [ ] User has reviewed staging folder

**If all checks pass**:
```bash
cd ..
git add .
git commit -m "release: v0.2.0-prealpha"
git push origin main
```

---

_Validated by_: ________________
_Date_: ________________

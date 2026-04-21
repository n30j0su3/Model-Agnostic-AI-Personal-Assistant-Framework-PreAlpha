# PA Framework v0.3.7-alpha HOTFIX3 — Final Release Checklist

> Date: 2026-04-21  
> Scope: `/home/freakingjson/Hermes-Stuff/staging/zip-review`  
> Artifact: `PA-Framework-v0.3.7-alpha-FINAL-HOTFIX3-20260421.zip`

## Executive Status

| **Campo** | **Valor** |
|---|---|
| **Release readiness** | ⚠️ Conditional (requires cleanup of root docs/version strings) |
| **Blockers (hard)** | 2 |
| **Warnings (should fix)** | 5 |
| **Passed checks** | 7 |
| **ZIP SHA256** | `5991392d0b2e8199755d381d1167fc9647ce2eaa2484b308b7b10d149f72e741` |

## Validation Matrix

| **ID** | **Check** | **Status** | **Evidence** | **Action** |
|---|---|---|---|---|
| C1 | Artefacto ZIP final existe | ✅ PASS | ZIP found (1,056,671 bytes) | — |
| C2 | `.opencode/package*.json` y locks necesarios | ⚠️ WARN | `.opencode/package.json` + `package-lock.json` present; `bun.lock` removed; no strong runtime coupling outside `.opencode` docs | Keep if `.opencode` is distributable runtime; otherwise move to optional profile |
| C3 | `config/branding.txt` versión | ✅ PASS | Banner shows `v0.3.7-alpha` | — |
| C4 | `config/framework.yaml` actualizado | ✅ PASS | Version header `0.3.7-alpha` + `memory_pipeline` block present | — |
| C5 | `config/i18n.json` integrado real | ⚠️ WARN | Release notes claim integration; no clear runtime load in `core/scripts/install.py`/menu flow detected | Wire into runtime loader + fallback locale |
| C6 | `config/user-settings.json` integrado real | ⚠️ WARN | Exists + referenced in self-healing checks, but no clear consumer flow in startup runtime | Add read/merge in `session_start.py` / `pa.py` |
| C7 | `design-system/design-system.css` ubicación/integración | ⚠️ WARN | File exists, no direct imports detected | Move to semantic assets path + import in dashboard/app |
| C8 | `examples/knowledge-management/search_examples.py` | ⚠️ WARN | Example file with references mostly documental | Keep under examples/docs only, not runtime bundle root |
| C9 | `skills/simple_research.toml` / `greet_user.toml` en raíz | ✅ PASS | Not present in root skills folder | — |
| C10 | `tests/` en raíz | ⚠️ WARN | Tests folder exists with low integration signals | Keep for dev distro; exclude/move for end-user runtime ZIP |
| C11 | `TEST-INSTRUCTIONS-v0.3.7-alpha.md` en raíz | ❌ FAIL | No external references | Move to `docs/qa/` and leave pointer in root |
| C12 | `VALIDATION-CHECKLIST.md` en raíz | ❌ FAIL | No external references | Move to `docs/qa/` and leave pointer in root |
| C13 | AGENTS tiers (lite/md/full) sin overlaps críticos | ✅ PASS | `AGENTS-lite.md` < `AGENTS.md` < `AGENTS-full.md`, bootstrap refs OK | — |
| C14 | Core/docs sin versión legacy operativa | ✅ PASS* | Legacy `v0.3.0-alpha` remains mainly in docs marked “Frozen” + historical release notes | Optional: relabel “frozen legacy APIs” to avoid confusion |

## Detected Legacy Version Strings (Non-blocking but visible)

- `core/scripts/install.py` header/banner still says `v0.3.0-alpha`.
- `docs/GETTING-STARTED.md`, `docs/CLI-INSTALL-GUIDE.md`, and docs/api pages still show `v0.3.0-alpha` (frozen context).

## Ship Recommendation

| **Campo** | **Valor** |
|---|---|
| **Can ship as-is?** | No (strict mode) / Yes (soft mode with known caveats) |
| **Strict requirement to ship** | Resolve C11 + C12 |
| **Strongly recommended before GA** | C5 + C6 + C7 + install.py version string refresh |

## 10-Point Quick Acceptance (for N30)

- [x] ZIP exists and hash generated
- [x] Branding version matches target
- [x] Framework config includes adaptive memory pipeline
- [x] AGENTS tier split is coherent (lite/router/full)
- [ ] Root QA docs relocated from root (C11/C12)
- [ ] i18n runtime consumption verified
- [ ] user-settings runtime consumption verified
- [ ] design-system semantic asset placement and import verified
- [x] Sample skill TOMLs removed from root
- [ ] install.py version strings aligned to v0.3.7-alpha

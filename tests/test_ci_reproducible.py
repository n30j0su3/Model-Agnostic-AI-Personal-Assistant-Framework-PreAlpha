"""CI and fresh-extract release gates must be reproducible from a clean tree."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_test_dependency_manifest_is_minimal_and_pinned():
    manifest = ROOT / "requirements-dev.txt"
    assert manifest.is_file()
    dependencies = [
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert dependencies == ["pytest==9.1.1"]


def test_fresh_extract_gate_runs_both_test_trees():
    source = (ROOT / "tests" / "gates" / "release_gate.py").read_text(encoding="utf-8")
    assert 'pytest_gate("R1", "tests", "core/scripts/tests"' in source

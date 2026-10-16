#!/usr/bin/env python3
"""Restore PA managed surfaces from a pre-migration snapshot."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKUPS_ROOT = REPO_ROOT / "data" / "backups"
MANDATORY_PROTECTED = (
    Path("core/.context/sessions"),
    Path("core/.context/memory"),
    Path("core/.context/knowledge/users"),
    Path("core/.context/knowledge/interactions-index.json"),
    Path("data/user"),
    Path("data/wizard"),
    Path("workspaces"),
)


def _safe_relative(value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe manifest path: {value!r}")
    return relative


def _is_protected(relative: Path, protected: tuple[Path, ...]) -> bool:
    return any(relative == prefix or prefix in relative.parents for prefix in protected)


def _restore_file(root: Path, source: Path, relative: Path, existed: bool) -> tuple[int, int]:
    target = root / relative
    if existed:
        if not source.is_file():
            raise ValueError(f"snapshot file missing: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return 1, 0
    if target.is_file() or target.is_symlink():
        target.unlink()
        return 0, 1
    return 0, 0


def _restore_directory(
    root: Path,
    source: Path,
    relative: Path,
    existed: bool,
    protected: tuple[Path, ...],
) -> tuple[int, int, int]:
    target = root / relative
    restored = removed = preserved = 0
    snapshot_files = {
        path.relative_to(source)
        for path in source.rglob("*")
        if path.is_file()
    } if source.is_dir() else set()

    if target.is_dir():
        current = sorted(target.rglob("*"), key=lambda path: len(path.parts), reverse=True)
        for path in current:
            repo_relative = path.relative_to(root)
            if _is_protected(repo_relative, protected):
                preserved += 1
                continue
            local = path.relative_to(target)
            if path.is_file() or path.is_symlink():
                if local not in snapshot_files:
                    path.unlink()
                    removed += 1
            elif path.is_dir() and not (source / local).is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass

    if not existed:
        if target.is_dir():
            try:
                target.rmdir()
            except OSError:
                pass
        return restored, removed, preserved

    target.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        for path in sorted(source.rglob("*")):
            local = path.relative_to(source)
            destination = target / local
            if path.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            elif path.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
                restored += 1
    return restored, removed, preserved


def restore_snapshot(snapshot: str | Path, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    backups_root = (root / "data" / "backups").resolve()
    snapshot_path = Path(snapshot)
    if not snapshot_path.is_absolute():
        snapshot_path = root / snapshot_path
    snapshot_path = snapshot_path.resolve()
    if snapshot_path != backups_root and backups_root not in snapshot_path.parents:
        raise ValueError("snapshot must be inside data/backups")

    manifest_path = snapshot_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or not isinstance(manifest.get("roots"), list):
        raise ValueError("unsupported or invalid snapshot manifest")

    manifest_protected = tuple(
        _safe_relative(value) for value in manifest.get("protected", [])
    )
    protected = tuple(dict.fromkeys((*MANDATORY_PROTECTED, *manifest_protected)))
    files_root = snapshot_path / "files"
    restored = removed = preserved = 0

    for entry in manifest["roots"]:
        relative = _safe_relative(entry["path"])
        if _is_protected(relative, protected):
            preserved += 1
            continue
        kind = entry.get("kind")
        existed = bool(entry.get("existed"))
        source = files_root / relative
        if kind == "file" or (kind == "missing" and relative.suffix):
            r_count, d_count = _restore_file(root, source, relative, existed)
            restored += r_count
            removed += d_count
        else:
            r_count, d_count, p_count = _restore_directory(
                root, source, relative, existed, protected
            )
            restored += r_count
            removed += d_count
            preserved += p_count

    return {
        "ok": True,
        "snapshot": str(snapshot_path),
        "restored": restored,
        "removed": removed,
        "preserved_protected": preserved,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore a PA migration snapshot")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = restore_snapshot(args.snapshot)
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(receipt, ensure_ascii=False))
        else:
            print(f"ROLLBACK FAILED: {exc}")
        return 2
    if args.json:
        print(json.dumps(receipt, ensure_ascii=False))
    else:
        print(f"ROLLBACK OK: {receipt['snapshot']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

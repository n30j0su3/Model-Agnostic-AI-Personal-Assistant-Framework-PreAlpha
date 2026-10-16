#!/usr/bin/env python3
"""Build and verify a deterministic sanitized public release ZIP."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_NAME = "MANIFEST.sha256.json"
TEXT_SUFFIXES = {".md", ".py", ".html", ".yaml", ".yml", ".json", ".txt", ".sh", ".ps1", ".bat", ".toml"}
BINARY_SUFFIXES = {
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".ttf",
    ".wav",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}
DENIED_PARTS = {".git", ".pytest_cache", "__pycache__", "node_modules", ".mypy_cache", ".ruff_cache"}
DENIED_ROOTS = {"data", "dist", "build", "backups"}
DENIED_NAMES = {
    ".env",
    ".env.local",
    "dashboard.token",
    "auth.json",
    "credentials.json",
    "AGENTS-full.md",
    "README-simple.md",
    "VALIDATION-CHECKLIST.md",
}
LOCAL_USER = b"freaking" + b"json"
LOCAL_PATH_NEEDLES = (
    b"/home/" + LOCAL_USER,
    b"/Users/" + LOCAL_USER,
    b"C:\\Users\\" + LOCAL_USER,
)
LOCAL_PATH_PATTERNS = (
    re.compile(rb"(?:/home/|/Users/)[A-Za-z0-9._-]+(?:/|\b)"),
    re.compile(rb"C:\\Users\\[A-Za-z0-9._-]+(?:\\|\b)", re.IGNORECASE),
)
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(rb"\bsk-[A-Za-z0-9]{24,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
)


class ReleaseBuildError(RuntimeError):
    """Release input or output violates the public package contract."""


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def is_denied_path(path: str) -> bool:
    normalized = PurePosixPath(path)
    parts = normalized.parts
    if not parts or normalized.is_absolute() or ".." in parts:
        return True
    if normalized.name == MANIFEST_NAME:
        return True
    if parts[0] in DENIED_ROOTS or DENIED_PARTS.intersection(parts):
        return True
    if normalized.name in DENIED_NAMES:
        return True
    if normalized.name == ".env" or normalized.name.startswith(".env."):
        return True
    lowered_name = normalized.name.lower()
    if ".bak" in lowered_name or lowered_name.endswith((".swp", ".tmp", "~")):
        return True
    if normalized.suffix.lower() in {
        ".db",
        ".key",
        ".log",
        ".pem",
        ".pyc",
        ".pyo",
        ".sqlite",
        ".sqlite3",
    }:
        return True
    if path.startswith((".opencode/auth", ".opencode/cache/", ".hermes/")):
        return True
    return False


def is_scannable_payload(path: str, payload: bytes) -> bool:
    """Scan every non-binary payload, including extensionless and JSONC files."""
    if PurePosixPath(path).suffix.lower() in BINARY_SUFFIXES:
        return False
    return b"\x00" not in payload[:8192]


def assert_public_payload(path: str, payload: bytes) -> None:
    if not is_scannable_payload(path, payload):
        return
    for needle in LOCAL_PATH_NEEDLES:
        if needle in payload:
            raise ReleaseBuildError(f"local path leaked in {path}")
    for pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(payload):
            raise ReleaseBuildError(f"local path leaked in {path}")
    for pattern in SECRET_PATTERNS:
        if pattern.search(payload):
            raise ReleaseBuildError(f"secret-like payload leaked in {path}")


def current_tree(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "write-tree"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def resolve_tree(repo_root: Path, treeish: str | None) -> str:
    if treeish is None:
        return current_tree(repo_root)
    return subprocess.run(
        ["git", "rev-parse", "--verify", f"{treeish}^{{tree}}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def archive_files(repo_root: Path, treeish: str) -> tuple[dict[str, tuple[bytes, int]], list[str]]:
    result = subprocess.run(
        ["git", "archive", "--format=tar", treeish],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )
    files: dict[str, tuple[bytes, int]] = {}
    excluded: list[str] = []
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            path = member.name
            if is_denied_path(path):
                excluded.append(path)
                continue
            stream = archive.extractfile(member)
            if stream is None:
                raise ReleaseBuildError(f"cannot read archived file: {path}")
            payload = stream.read()
            assert_public_payload(path, payload)
            files[path] = (payload, member.mode & 0o777)
    return files, sorted(excluded)


def _zip_info(path: str, mode: int = 0o644) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (mode & 0xFFFF) << 16
    return info


def build_release_zip(
    output_dir: Path | str,
    *,
    treeish: str | None = None,
    repo_root: Path = REPO_ROOT,
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    resolved_tree = resolve_tree(repo_root, treeish)
    files, excluded = archive_files(repo_root, resolved_tree)
    if "VERSION" not in files:
        raise ReleaseBuildError("VERSION is missing from release tree")
    version = files["VERSION"][0].decode("utf-8").strip()
    manifest: dict[str, Any] = {
        "schema": 1,
        "version": version,
        "tree": resolved_tree,
        "files": [
            {"path": path, "size": len(payload), "sha256": sha256(payload)}
            for path, (payload, _mode) in sorted(files.items())
        ],
        "excluded": excluded,
    }
    manifest_payload = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    package = output / f"pa-framework-{version}.zip"
    with zipfile.ZipFile(package, "w") as target:
        for path, (payload, mode) in sorted(files.items()):
            target.writestr(_zip_info(path, mode), payload)
        target.writestr(_zip_info(MANIFEST_NAME), manifest_payload)
    return package


def verify_release_zip(package: Path | str) -> dict[str, Any]:
    path = Path(package)
    payload = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ReleaseBuildError("duplicate ZIP member")
        if MANIFEST_NAME not in names:
            raise ReleaseBuildError("manifest missing")
        if any(name != MANIFEST_NAME and is_denied_path(name) for name in names):
            raise ReleaseBuildError("denied path present in ZIP")
        manifest = json.loads(archive.read(MANIFEST_NAME))
        expected = {entry["path"]: entry for entry in manifest["files"]}
        if set(names) != {*expected, MANIFEST_NAME}:
            raise ReleaseBuildError("ZIP/member manifest mismatch")
        for member, entry in expected.items():
            member_payload = archive.read(member)
            if len(member_payload) != entry["size"]:
                raise ReleaseBuildError(f"size mismatch: {member}")
            if sha256(member_payload) != entry["sha256"]:
                raise ReleaseBuildError(f"hash mismatch: {member}")
            assert_public_payload(member, member_payload)
    return {
        "path": str(path.resolve()),
        "size": len(payload),
        "sha256": sha256(payload),
        "files": len(manifest["files"]),
        "tree": manifest["tree"],
        "version": manifest["version"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "dist")
    parser.add_argument("--treeish")
    args = parser.parse_args(argv)
    package = build_release_zip(args.output_dir, treeish=args.treeish)
    print(json.dumps(verify_release_zip(package), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

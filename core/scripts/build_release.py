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
# OpenCode rewrites its own package.json/package-lock.json to the CLI version.
# They must ship for the bootstrap, but hashing them in the release manifest
# would fail after any real launch. They are covered by a semver contract
# instead of a byte-level hash.
VOLATILE_RUNTIME_PATHS = frozenset(
    {
        ".opencode/package.json",
        ".opencode/package-lock.json",
    }
)
OPENCODE_MIN_VERSION = (1, 18, 0)
VOLATILE_CONTRACTS = {
    path: "opencode-plugin>=%s" % ".".join(map(str, OPENCODE_MIN_VERSION))
    for path in VOLATILE_RUNTIME_PATHS
}
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
# Runtime/private paths are generated state, not release payload. ``data`` is
# root-only because core/skills/ui-ux-pro-max/data contains required assets.
DENIED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "backups",
    "logs",
    "node_modules",
}
DENIED_ROOTS = {"data", "dist", "build"}
DENIED_PREFIXES = (
    ("core", ".context", "sessions"),
    ("core", ".context", ".cache"),
    ("core", ".context", "knowledge", "errors"),
)
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
# RC6-1 semantic privacy frontier: ``core/.context`` ships an exact public
# allowlist (templates, seeds, .gitkeep scaffolding, static docs/indexes).
# Any tracked path under core/.context outside this set is private runtime
# state and fails closed: excluded from the package and recorded in the
# manifest, even if it was committed by accident.
CONTEXT_PUBLIC_PREFIX = "core/.context/"
CONTEXT_PUBLIC_PATHS = frozenset(
    {
        "core/.context/.gitkeep",
        "core/.context/MASTER.template.md",
        "core/.context/codebase/backlog.seed.md",
        "core/.context/knowledge/.gitkeep",
        "core/.context/knowledge/README.md",
        "core/.context/knowledge/learning/.gitkeep",
        "core/.context/knowledge/prompts/.gitkeep",
        "core/.context/knowledge/self-healing/.gitkeep",
        "core/.context/knowledge/wiki/README.md",
        "core/.context/knowledge/wiki/comparisons/.gitkeep",
        "core/.context/knowledge/wiki/concepts/.gitkeep",
        "core/.context/knowledge/wiki/entities/.gitkeep",
        "core/.context/knowledge/wiki/queries/.gitkeep",
        "core/.context/knowledge/wiki/raw/extracts/.gitkeep",
        "core/.context/knowledge/wiki/raw/inputs/.gitkeep",
        "core/.context/knowledge/wiki/raw/observations/.gitkeep",
        "core/.context/navigation.md",
        "core/.context/opencode-reference.md",
        "core/.context/profile.template.md",
        "core/.context/quick-start.md",
    }
)
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


_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def _parse_semver(value: str, *, context: str) -> tuple[int, int, int]:
    match = _SEMVER_RE.search(value or "")
    if match is None:
        raise ReleaseBuildError(f"invalid OpenCode version in {context}: {value!r}")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _assert_min_opencode_version(path: str, value: str) -> None:
    found = _parse_semver(value, context=path)
    if found < OPENCODE_MIN_VERSION:
        minimum = ".".join(map(str, OPENCODE_MIN_VERSION))
        raise ReleaseBuildError(
            f"OpenCode plugin {value} in {path} is below the release minimum {minimum}"
        )


def validate_volatile_runtime_payload(path: str, payload: bytes) -> None:
    """Validate a runtime-managed OpenCode file without freezing its bytes."""
    if path not in VOLATILE_RUNTIME_PATHS:
        raise ReleaseBuildError(f"not a runtime-managed path: {path}")
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseBuildError(f"invalid JSON in {path}: {exc}") from exc
    if path == ".opencode/package.json":
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        _assert_min_opencode_version(path, str(deps.get("@opencode-ai/plugin", "")))
        return
    packages = data.get("packages")
    if not isinstance(packages, dict):
        raise ReleaseBuildError(f"invalid package-lock structure in {path}")
    for name in ("@opencode-ai/plugin", "@opencode-ai/sdk"):
        entry = packages.get(f"node_modules/{name}")
        if not isinstance(entry, dict) or "version" not in entry:
            raise ReleaseBuildError(f"missing {name} in {path}")
        _assert_min_opencode_version(path, str(entry["version"]))


def is_denied_context_path(path: str) -> bool:
    """Fail-closed semantic allowlist for the core/.context runtime root."""
    return path.startswith(CONTEXT_PUBLIC_PREFIX) and path not in CONTEXT_PUBLIC_PATHS


def is_denied_path(path: str) -> bool:
    normalized = PurePosixPath(path)
    parts = normalized.parts
    if not parts or normalized.is_absolute() or ".." in parts:
        return True
    if normalized.name == MANIFEST_NAME:
        return True
    if is_denied_context_path(path):
        return True
    if parts[0] in DENIED_ROOTS or DENIED_PARTS.intersection(parts):
        return True
    if any(parts[: len(prefix)] == prefix for prefix in DENIED_PREFIXES):
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
    missing_volatile = VOLATILE_RUNTIME_PATHS.difference(files)
    if missing_volatile:
        raise ReleaseBuildError(
            f"runtime-managed OpenCode files missing: {sorted(missing_volatile)}"
        )
    for path in sorted(VOLATILE_RUNTIME_PATHS):
        validate_volatile_runtime_payload(path, files[path][0])
    manifest: dict[str, Any] = {
        "schema": 2,
        "version": version,
        "tree": resolved_tree,
        "files": [
            {"path": path, "size": len(payload), "sha256": sha256(payload)}
            for path, (payload, _mode) in sorted(files.items())
            if path not in VOLATILE_RUNTIME_PATHS
        ],
        "volatile": [
            {"path": path, "contract": VOLATILE_CONTRACTS[path]}
            for path in sorted(VOLATILE_RUNTIME_PATHS)
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
        if manifest.get("schema") != 2:
            raise ReleaseBuildError("unsupported manifest schema")
        expected = {entry["path"]: entry for entry in manifest["files"]}
        volatile = {entry["path"]: entry for entry in manifest.get("volatile", [])}
        if set(volatile) != set(VOLATILE_RUNTIME_PATHS):
            raise ReleaseBuildError("volatile manifest mismatch")
        if set(names) != {*expected, *volatile, MANIFEST_NAME}:
            raise ReleaseBuildError("ZIP/member manifest mismatch")
        for member, entry in expected.items():
            member_payload = archive.read(member)
            if len(member_payload) != entry["size"]:
                raise ReleaseBuildError(f"size mismatch: {member}")
            if sha256(member_payload) != entry["sha256"]:
                raise ReleaseBuildError(f"hash mismatch: {member}")
            assert_public_payload(member, member_payload)
        for member in volatile:
            member_payload = archive.read(member)
            validate_volatile_runtime_payload(member, member_payload)
            assert_public_payload(member, member_payload)
    return {
        "path": str(path.resolve()),
        "size": len(payload),
        "sha256": sha256(payload),
        "files": len(expected),
        "volatile": len(volatile),
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

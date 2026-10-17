"""Portable exclusion contracts for FileLock."""

from __future__ import annotations

import ctypes
import errno
import json
import multiprocessing
import os
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from core.scripts.file_lock import FileLock, LockInfo


def _contending_worker(resource: str, start, hold, results, instance_id: str) -> None:
    lock = FileLock(resource, instance_id=instance_id)
    start.wait(10)
    acquired = lock.acquire(timeout=0.5, blocking=False)
    results.put((instance_id, acquired))
    if acquired:
        hold.wait(10)
        lock.release()


def test_same_basename_uses_distinct_absolute_lock_paths(tmp_path: Path, monkeypatch):
    lock_dir = tmp_path / "locks"
    monkeypatch.setenv("PA_FRAMEWORK_LOCK_DIR", str(lock_dir))

    first = FileLock(str(tmp_path / "one" / "same.json"), instance_id="one")
    second = FileLock(str(tmp_path / "two" / "same.json"), instance_id="two")

    assert first.lock_path.is_absolute()
    assert second.lock_path.is_absolute()
    assert first.lock_path.parent == lock_dir.resolve()
    assert first.lock_path != second.lock_path


def test_is_locked_does_not_delete_expired_or_malformed_lock(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PA_FRAMEWORK_LOCK_DIR", str(tmp_path / "locks"))
    lock = FileLock(str(tmp_path / "resource.json"), instance_id="observer")
    expired = LockInfo(
        instance_id="owner",
        pid=os.getpid(),
        timestamp=(datetime.now() - timedelta(minutes=5)).isoformat(),
        timeout=0.01,
        resource=str(lock.resource_path),
    )
    lock.lock_path.write_text(json.dumps(expired.to_dict()), encoding="utf-8")
    before = lock.lock_path.read_bytes()

    assert lock.is_locked() is False
    assert lock.lock_path.read_bytes() == before

    lock.lock_path.write_text("{malformed", encoding="utf-8")
    malformed = lock.lock_path.read_bytes()
    assert lock.is_locked() is False
    assert lock.lock_path.read_bytes() == malformed
    contender = FileLock(str(tmp_path / "resource.json"), instance_id="contender")
    assert contender.acquire(timeout=0.0, blocking=False) is False
    assert lock.lock_path.read_bytes() == malformed


def test_process_permission_errors_are_fail_closed(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PA_FRAMEWORK_LOCK_DIR", str(tmp_path / "locks"))
    lock = FileLock(str(tmp_path / "resource.json"), instance_id="observer")

    def deny_posix(_pid: int, _signal: int) -> None:
        raise PermissionError(errno.EPERM, "synthetic permission denied")

    monkeypatch.setattr(os, "kill", deny_posix)
    assert lock._is_process_alive_posix(12345) is True

    class Kernel32:
        @staticmethod
        def OpenProcess(*_args):
            return 0

        @staticmethod
        def CloseHandle(_handle):
            raise AssertionError("zero handle must not be closed")

    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(kernel32=Kernel32()), raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    assert lock._is_process_alive_windows(12345) is True


def test_exclusive_create_refuses_existing_owner(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PA_FRAMEWORK_LOCK_DIR", str(tmp_path / "locks"))
    resource = str(tmp_path / "shared.json")
    first = FileLock(resource, instance_id="first")
    second = FileLock(resource, instance_id="second")
    first_info = LockInfo(
        instance_id="first",
        pid=os.getpid(),
        timestamp=datetime.now().isoformat(),
        timeout=30.0,
        resource=str(first.resource_path),
    )
    second_info = LockInfo(
        instance_id="second",
        pid=os.getpid(),
        timestamp=datetime.now().isoformat(),
        timeout=30.0,
        resource=str(second.resource_path),
    )

    assert first._try_create_exclusive(first_info) is True
    assert second._try_create_exclusive(second_info) is False
    assert json.loads(first.lock_path.read_text(encoding="utf-8"))["instance_id"] == "first"


def test_two_processes_cannot_acquire_same_resource(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PA_FRAMEWORK_LOCK_DIR", str(tmp_path / "locks"))
    resource = str(tmp_path / "shared.json")
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    hold = context.Event()
    results = context.Queue()
    workers = [
        context.Process(
            target=_contending_worker,
            args=(resource, start, hold, results, f"worker-{index}"),
        )
        for index in range(2)
    ]
    for worker in workers:
        worker.start()
    start.set()
    observed = [results.get(timeout=15) for _ in workers]
    hold.set()
    for worker in workers:
        worker.join(timeout=15)
        assert worker.exitcode == 0

    assert sum(acquired for _instance, acquired in observed) == 1, observed

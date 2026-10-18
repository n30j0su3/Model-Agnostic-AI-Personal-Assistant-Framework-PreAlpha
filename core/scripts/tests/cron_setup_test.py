"""Fail-closed contracts for Linux cron ownership."""

import platform
from types import SimpleNamespace

from core.scripts import cron_setup


UNMANAGED = (
    "MAILTO=ops@example.test\n"
    "# unrelated backup containing the product name\n"
    "0 2 * * * /usr/local/bin/pa-framework-backup\n"
)


def _runner(current_crontab: str, write_returncode: int = 0):
    platform.system()
    writes = []

    def fake_run(command, **kwargs):
        if command == ["crontab", "-l"]:
            return SimpleNamespace(returncode=0, stdout=current_crontab, stderr="")
        if command == ["crontab", "-"]:
            writes.append(kwargs["input"])
            return SimpleNamespace(
                returncode=write_returncode,
                stdout="",
                stderr="write denied" if write_returncode else "",
            )
        raise AssertionError(f"unexpected command: {command}")

    return fake_run, writes


def test_runner_primes_platform_identity_before_subprocess_is_faked(monkeypatch):
    monkeypatch.setattr(platform, "_uname_cache", None, raising=False)

    _runner(UNMANAGED)

    assert getattr(platform, "_uname_cache", None) is not None


def test_setup_replaces_only_pa_owned_linux_cron_entries(monkeypatch):
    legacy = (
        UNMANAGED
        + "# PA Framework Crons\n"
        + "# PA-Learning-Cron\n"
        + "*/99 * * * * /old/python /old/learning_cron.py --run\n"
    )
    fake_run, writes = _runner(legacy)
    monkeypatch.setattr(cron_setup.subprocess, "run", fake_run)
    setup = cron_setup.CronSetup()

    result = setup._setup_linux()

    assert result["success"] is True
    assert len(writes) == 1
    rendered = writes[0]
    assert UNMANAGED in rendered
    assert "*/99 * * * *" not in rendered
    assert rendered.count(cron_setup.CRON_BLOCK_BEGIN) == 1
    assert rendered.count(cron_setup.CRON_BLOCK_END) == 1
    for job in cron_setup.CRON_JOBS:
        assert rendered.count(f"# {job['name']}") == 1


def test_setup_fails_closed_when_crontab_rejects_write(monkeypatch):
    fake_run, _ = _runner(UNMANAGED, write_returncode=1)
    monkeypatch.setattr(cron_setup.subprocess, "run", fake_run)

    result = cron_setup.CronSetup()._setup_linux()

    assert result["success"] is False
    assert "write denied" in result["error"]


def test_remove_preserves_every_unmanaged_linux_cron_line(monkeypatch):
    managed = (
        f"{cron_setup.CRON_BLOCK_BEGIN}\n"
        "# PA-Learning-Cron\n"
        "*/5 * * * * /python /repo/learning_cron.py --run\n"
        f"{cron_setup.CRON_BLOCK_END}\n"
    )
    fake_run, writes = _runner(UNMANAGED + managed)
    monkeypatch.setattr(cron_setup.subprocess, "run", fake_run)
    setup = cron_setup.CronSetup()
    setup.platform = "Linux"

    result = setup.remove_all()

    assert result["success"] is True
    assert writes == [UNMANAGED]

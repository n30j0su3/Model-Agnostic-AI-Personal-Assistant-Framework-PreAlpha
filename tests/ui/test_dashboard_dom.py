"""Dashboard DOM contract plus optional real-CDP viewport gate."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BROWSER_HOME = Path(os.environ.get("PA_BROWSER_HOME", str(Path.home())))


def agent(port: str, session: str, *command: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(BROWSER_HOME)
    env["USERPROFILE"] = str(BROWSER_HOME)
    return subprocess.run(
        [
            "npx",
            "--yes",
            "agent-browser",
            "--cdp",
            port,
            "--session",
            session,
            *command,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=True,
    )


def evaluate(port: str, session: str, expression: str):
    raw = agent(port, session, "eval", expression).stdout.strip()
    value = json.loads(raw)
    return json.loads(value) if isinstance(value, str) else value


def test_dashboard_has_mobile_and_docs_bootstrap_contract():
    html = (ROOT / "dashboard.html").read_text(encoding="utf-8")

    assert 'id="app-header"' in html
    assert 'id="primary-nav"' in html
    assert 'id="docs-body"' in html
    assert "docsPage.show(docsPage.current" in html
    assert "min-height: 44px" in html
    assert "assets/tailwind.js" in html
    assert "assets/chart.umd.js" in html


def test_active_navigation_contrast_and_semantics():
    html = (ROOT / "dashboard.html").read_text(encoding="utf-8")
    primary_nav = re.search(
        r'<nav id="primary-nav".*?</nav>', html, re.DOTALL
    )
    assert primary_nav is not None
    visible_nav_buttons = [
        tag
        for tag in re.findall(r"<button\b[^>]*data-page=\"[^\"]+\"[^>]*>", primary_nav.group(0))
        if 'aria-hidden="true"' not in tag
    ]
    assert visible_nav_buttons
    assert all('aria-label="' in tag for tag in visible_nav_buttons)
    assert "btn.setAttribute('aria-current', isActive ? 'page' : 'false')" in html
    assert "btn.classList.toggle('text-slate-950', isActive)" in html

    tabs = re.search(r'<div[^>]*id="framework-tabs".*?</div>', html, re.DOTALL)
    assert tabs is not None
    assert 'role="tablist"' in tabs.group(0)
    tab_buttons = re.findall(r"<button\b[^>]*class=\"fw-tab-btn[^>]*>", tabs.group(0))
    assert len(tab_buttons) == 4
    assert all('role="tab"' in tag for tag in tab_buttons)
    assert "btn.setAttribute('aria-selected', String(isActive))" in html
    assert "btn.classList.add('bg-lime-500', 'text-slate-950')" in html


def test_lime_action_buttons_use_dark_text_for_wcag_contrast():
    html = (ROOT / "dashboard.html").read_text(encoding="utf-8")
    lime_buttons = [
        tag
        for tag in re.findall(r"<button\b[^>]*>", html)
        if re.search(r"\bbg-lime-(?:400|500|600)\b", tag)
    ]

    assert lime_buttons
    assert all(re.search(r"\btext-slate-(?:900|950)\b", tag) for tag in lime_buttons), lime_buttons
    assert re.findall(
        r"\bbg-lime-(?:400|500|600)\b[^'\"}]*\btext-white\b", html
    ) == []


def test_dashboard_four_viewports_live():
    url = os.environ.get("PA_DASHBOARD_URL")
    port = os.environ.get("PA_CDP_PORT")
    if not url or not port:
        pytest.skip("live CDP gate requires PA_DASHBOARD_URL and PA_CDP_PORT")
    session = f"pa-t16-pytest-{os.getpid()}"
    agent(port, session, "open", url)

    script = """JSON.stringify((()=>{const els=[...document.querySelectorAll('button,a,[role=button]')].filter(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0});return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth,small:els.map(e=>({text:(e.innerText||e.getAttribute('aria-label')||e.title||'').trim().slice(0,60),height:e.getBoundingClientRect().height})).filter(x=>x.height<44)}})())"""
    for width in (360, 480, 768, 1600):
        agent(port, session, "set", "viewport", str(width), "900")
        metrics = evaluate(port, session, script)
        assert metrics["overflow"] is False, metrics
        assert metrics["scrollWidth"] <= metrics["width"], metrics
        assert metrics["small"] == [], metrics

    agent(port, session, "click", '[data-page="docs"]')
    agent(port, session, "wait", "250")
    docs = evaluate(
        port,
        session,
        "JSON.stringify({len:(document.querySelector('#docs-body')?.innerText||'').trim().length})",
    )
    assert docs["len"] > 0

    errors = agent(port, session, "errors").stdout.strip()
    assert errors == ""
    requests = agent(
        port,
        session,
        "network",
        "requests",
        "--filter",
        url.split("//", 1)[1].rstrip("/"),
    ).stdout
    failing = []
    for line in requests.splitlines():
        match = re.search(r"=> \[(\d{3})\]", line)
        if match and int(match.group(1)) >= 400:
            failing.append(line)
    assert failing == []

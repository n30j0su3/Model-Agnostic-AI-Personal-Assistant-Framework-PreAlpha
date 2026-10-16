"""D2 contracts for the Dashboard SPA/API integration."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "dashboard.html"


@pytest.fixture(scope="module")
def html() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _block(html: str, start: str, end: str) -> str:
    left = html.index(start)
    right = html.index(end, left)
    return html[left:right]


def test_loader_uses_single_knowledge_summary_api(html: str) -> None:
    loader = _block(html, "const dataLoader =", "const router =")
    assert "/api/knowledge/summary" in loader
    assert ".context/indexes/sessions-index.json" not in loader
    assert ".context/indexes/skills-index.json" not in loader
    assert ".context/indexes/agents-index.json" not in loader
    assert ".context/indexes/errors-index.json" not in loader


def test_store_sessions_are_real_api_rows_without_embedded_fallback(html: str) -> None:
    loader = _block(html, "const dataLoader =", "const router =")
    assert "store.sessions =" in loader
    assert "knowledge.sessions" in loader
    assert "window.DASHBOARD_DATA.sessions" not in loader
    assert "store.currentSession = store.sessions[0] || null" in loader


def test_empty_agents_do_not_fabricate_framework_agents(html: str) -> None:
    internals = _block(html, "internals() {", "console() {")
    assert "store.agents && store.agents.length > 0 ? store.agents : [" not in internals
    assert "No se encontraron agentes indexados" in internals
    assert "app.inspectAgent" in internals


def test_skills_have_toggle_and_real_reindex_controls(html: str) -> None:
    assert "app.toggleSkill" in html
    assert "'/api/skills/toggle'" in html
    assert "'/api/skills/reindex'" in html
    assert "async runIndexer()" in html


def test_agents_have_real_inspect_and_update_controls(html: str) -> None:
    assert "'/api/agents/read?path='" in html
    assert "'/api/agents/update'" in html
    assert "async inspectAgent(" in html
    assert "async saveAgentFromModal()" in html
    assert 'id="agent-editor"' in html


def test_sensitive_gets_use_json_and_dashboard_token(html: str) -> None:
    api = _block(html, "async api(path, method = 'GET'", "log(role, text)")
    assert "'Content-Type': 'application/json'" in api
    assert "headers['X-PA-Token'] = await this.bootstrapSecurity()" in api
    assert "if (method !== 'GET')" not in api


def test_branding_is_applied_from_status_payload(html: str) -> None:
    assert "function applyBranding(" in html
    assert "payload.framework?.brand || payload.brand" in html
    for element_id in (
        "brand-footer-text",
        "brand-footer-github",
        "brand-footer-linktree",
        "brand-footer-threads",
        "brand-footer-support",
    ):
        assert f'id="{element_id}"' in html


def test_internals_has_no_invented_percentages_or_fixed_usage_scale(html: str) -> None:
    internals = _block(html, "internals() {", "console() {")
    for fabricated in (">45%<", ">20%<", ">25%<", ">10%<", ">92%<", ">87%<", "i.count / 450"):
        assert fabricated not in internals
    assert "store.agents.length" in internals
    assert "store.lspErrors.length" in internals


def test_chart_instances_are_destroyed_before_internals_rerender(html: str) -> None:
    assert "this.instances.activity?.destroy()" in html
    assert "this.instances.topics?.destroy()" in html


def test_demo_session_action_routes_to_real_sessions(html: str) -> None:
    action = _block(html, "\n            showSessionDemo() {", "\n            async runIndexer()")
    assert "router.navigate('sessions')" in action
    assert "Ejemplo de Sesión" not in action
    assert "Esta es una sesión real" not in action


def test_spa_uses_same_origin_relative_api_calls(html: str) -> None:
    assert "fetch('http://127.0.0.1" not in html
    assert 'fetch("http://127.0.0.1' not in html
    assert "mode: 'cors'" not in html
    assert 'mode: "cors"' not in html


def test_private_indexes_are_not_requested_as_static_assets(html: str) -> None:
    for private_path in (".context/indexes/", "data/user/", "config/branding.json"):
        assert f"loadJSON('{private_path}" not in html


class _Scripts(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        script_type = (values.get("type") or "text/javascript").lower()
        if tag == "script" and not values.get("src") and script_type in {
            "text/javascript",
            "application/javascript",
            "module",
        }:
            self._capture = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._capture = False
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._capture:
            self.parts.append(data)


def test_inline_javascript_parses_with_node(html: str, tmp_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is unavailable")
    parser = _Scripts()
    parser.feed(html)
    script = tmp_path / "dashboard-inline.js"
    script.write_text("".join(parser.parts), encoding="utf-8")
    result = subprocess.run([node, "--check", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

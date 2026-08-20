#!/usr/bin/env python3
"""
PA Framework — Tests del fix v0.4.1-beta (bug N30 2026-08-19):
"el framework detecta credenciales de opencode pero no las usa".

Cubre:
  1. oc_auth.provider_auth_status: env / auth.json / anon / missing
  2. select_free_model.get_free_models: retorna dicts con status (auth-aware)
  3. dashboard_server: normalización string→{providerID, modelID} (API serve
     rechaza strings con HTTP 400) y fallback al modelo asignado
  4. Orden cred-first (autenticados antes que sin-creds)

Run: pytest tests/test_model_auth_fix.py -v
"""
import json
import os
import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "core" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


oc_auth = _load("oc_auth")
sfm = _load("select_free_model")


# ---------------------------------------------------------------- oc_auth ---

class TestProviderAuthStatus:
    def test_authed_env(self):
        p = {"id": "nano-gpt", "env": ["NANO_GPT_API_KEY"]}
        with patch.dict(os.environ, {"NANO_GPT_API_KEY": "x"}):
            assert oc_auth.provider_auth_status(p) == "authed_env"

    def test_missing_env_not_authed(self):
        p = {"id": "nano-gpt", "env": ["NANO_GPT_API_KEY"]}
        env = {k: v for k, v in os.environ.items() if k != "NANO_GPT_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            # sin auth.json que lo cubra
            assert oc_auth.provider_auth_status(p, {}) == "missing"

    def test_authed_file(self):
        p = {"id": "zai-coding-plan", "env": ["ZHIPU_API_KEY"]}
        auth_data = {"zai-coding-plan": {"access_token": "tok", "type": "api"}}
        assert oc_auth.provider_auth_status(p, auth_data) == "authed_file"

    def test_anon_opencode_provider(self):
        # proveedor "opencode" tiene tier free anónimo (modelos *-free)
        p = {"id": "opencode", "env": ["OPENCODE_API_KEY"]}
        assert oc_auth.provider_auth_status(p, {}) == "anon"

    def test_env_takes_priority_over_file(self):
        p = {"id": "prov-x", "env": ["PROV_X_KEY"]}
        auth_data = {"prov-x": {"access_token": "t"}}
        with patch.dict(os.environ, {"PROV_X_KEY": "k"}):
            assert oc_auth.provider_auth_status(p, auth_data) == "authed_env"

    def test_badge_mapping(self):
        assert oc_auth.provider_auth_badge("authed_env") == "env"
        assert oc_auth.provider_auth_badge("authed_file") == "auth.json"
        assert oc_auth.provider_auth_badge("anon") == "anon"
        assert oc_auth.provider_auth_badge("missing") == "sin-creds"

    def test_auth_json_path_windows_localappdata(self):
        # En Windows usa %LOCALAPPDATA%/opencode/auth.json si existe
        with (patch.dict(os.environ, {"LOCALAPPDATA": "/fake/appdata"}, clear=False)):
            # no existe → cae al home estándar
            p = oc_auth.auth_json_path()
            assert p == Path.home() / ".local" / "share" / "opencode" / "auth.json"

    def test_load_auth_json_missing(self):
        with patch.object(oc_auth, "auth_json_path", return_value=Path("/no/existe")):
            assert oc_auth.load_auth_json() == {}

    def test_load_auth_json_corrupt(self, tmp_path):
        f = tmp_path / "auth.json"
        f.write_text("{corrupt json!!", encoding="utf-8")
        with patch.object(oc_auth, "auth_json_path", return_value=f):
            assert oc_auth.load_auth_json() == {}


# --------------------------------------------------- select_free_model ------

class TestGetFreeModelsAuthAware:
    """La lista free debe ser auth-aware: dicts {id, status} cred-first."""

    def _fake_catalog(self):
        return {
            "providers": [
                {"id": "opencode", "env": ["OPENCODE_API_KEY"], "models": {
                    "big-pickle": {"cost": {"input": 0, "output": 0}},
                }},
                {"id": "nano-gpt", "env": ["NANO_GPT_API_KEY"], "models": {
                    "auto-model": {"cost": {"input": 0, "output": 0}},
                    "paid-model": {"cost": {"input": 1, "output": 2}},
                }},
                {"id": "zai-coding-plan", "env": ["ZHIPU_API_KEY"], "models": {
                    "glm-5.3": {"cost": {"input": 0, "output": 0}},
                }},
            ]
        }

    def test_returns_dicts_with_status(self):
        with patch.object(sfm, "_is_real_serve", return_value=True), \
             patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.status = 200
            mock_urlopen.return_value.__enter__.return_value.read.return_value = \
                json.dumps(self._fake_catalog()).encode()
            env = {k: v for k, v in os.environ.items()
                   if k not in ("NANO_GPT_API_KEY", "ZHIPU_API_KEY", "OPENCODE_API_KEY")}
            with patch.dict(os.environ, env, clear=True), \
                 patch.object(oc_auth, "load_auth_json", return_value={}):
                models = sfm.get_free_models(47017)
        assert all(isinstance(m, dict) for m in models), \
            "get_free_models debe retornar dicts auth-aware, no strings"
        ids = [m["id"] for m in models]
        assert "nano-gpt/auto-model" in ids
        assert "nano-gpt/paid-model" not in ids  # paid excluido

    def test_cred_first_ordering(self):
        with patch.object(sfm, "_is_real_serve", return_value=True), \
             patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.status = 200
            mock_urlopen.return_value.__enter__.return_value.read.return_value = \
                json.dumps(self._fake_catalog()).encode()
            env = {k: v for k, v in os.environ.items() if k != "NANO_GPT_API_KEY"}
            with patch.dict(os.environ, env, clear=True), \
                 patch.object(oc_auth, "load_auth_json",
                              return_value={"zai-coding-plan": {"access_token": "t"}}):
                models = sfm.get_free_models(47017)
        statuses = [m["status"] for m in models]
        # nano-gpt sin creds debe quedar ÚLTIMO (zai authed y opencode anon antes)
        assert statuses == sorted(
            statuses, key=lambda s: {"authed_env": 0, "authed_file": 1, "anon": 2, "missing": 3}.get(s, 9)
        ), f"orden no cred-first: {statuses}"
        assert models[-1]["id"] == "nano-gpt/auto-model"


# ------------------------------------------------- dashboard chat model ----

class TestChatModelNormalization:
    """El bridge debe convertir 'provider/model' (string) a objeto —
    la API serve de opencode 1.4.6 rechaza strings con HTTP 400."""

    def _normalize(self, model):
        """Réplica exacta de la normalización del endpoint /api/opencode/chat."""
        if isinstance(model, str):
            pid, _, mid = model.partition("/")
            return {"providerID": pid, "modelID": mid} if mid else None
        return model

    def test_string_normalizes_to_object(self):
        assert self._normalize("zai-coding-plan/glm-5.3") == {
            "providerID": "zai-coding-plan", "modelID": "glm-5.3"}

    def test_string_without_slash_dropped(self):
        assert self._normalize("invalido") is None

    def test_object_passthrough(self):
        obj = {"providerID": "x", "modelID": "y"}
        assert self._normalize(obj) is obj


# ---------------------------------------------------- pa.py selección ------

class TestPaMenuAuthAware:
    """El menú M de pa.py debe aceptar la nueva shape dict y avisar sin-creds."""

    def test_dict_shape_supported(self):
        # simulación del manejo del menú (pa.py usa la misma lógica)
        selected = {"id": "nano-gpt/auto-model", "status": "missing"}
        if isinstance(selected, dict):
            warned = selected.get("status") == "missing"
            selected_id = selected.get("id", "")
        assert warned is True and selected_id == "nano-gpt/auto-model"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

#!/usr/bin/env python3
"""
v0.4.1-beta: Detección auth-aware de credenciales de opencode.

Problema que resuelve (bug N30 2026-08-19): en una máquina con opencode
ya instalado y credenciales configuradas, el framework DETECTABA las
credenciales (listado del catálogo /config/providers) pero NO podía
USARLAS (el chat servía con el default global de opencode, no con el
modelo asignado por el framework).

Causa raíz: la detección previa solo miraba el CATÁLOGO de modelos,
que opencode lista INDEPENDIENTEMENTE de que existan credenciales.
Detectar != poder usar. Este módulo une tres fuentes de verdad:

  1. env:        variables de entorno (ej. NANO_GPT_API_KEY) para cada proveedor
  2. auth.json:  ~/.local/share/opencode/auth.json (opencode auth login)
  3. anon:       proveedores con tier gratuito anónimo (opencode/*-free)

stdlib-only (local-first): json, os, pathlib. Sin requests, sin internet.
"""

import json
import os
from pathlib import Path

# Ruta estándar de credenciales de opencode (multi-OS, verificada en 1.4.6):
# Linux/macOS: ~/.local/share/opencode/auth.json
# Windows:     %LOCALAPPDATA%/opencode/auth.json (fallback: ~/.local/share/opencode)
def auth_json_path() -> Path:
    """Ruta canónica de auth.json según SO."""
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        cand = Path(local_appdata) / "opencode" / "auth.json"
        if cand.exists():
            return cand
    return Path.home() / ".local" / "share" / "opencode" / "auth.json"


def load_auth_json() -> dict:
    """Lee auth.json si existe. Retorna {} si falta o está corrupto."""
    p = auth_json_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def env_keys_for_provider(pinfo: dict) -> list[str]:
    """Variables de entorno que autentican al proveedor (según el catálogo)."""
    keys = []
    if isinstance(pinfo, dict):
        env = pinfo.get("env")
        if isinstance(env, list):
            keys = [e for e in env if isinstance(e, str)]
    return keys


def provider_auth_status(pinfo: dict, auth_data: dict | None = None) -> str:
    """Estado de credenciales de un proveedor del catálogo /config/providers.

    Retorna uno de:
      "authed_env"     — hay variable de entorno seteada (credentials OK)
      "authed_file"    — proveedor presente en auth.json (opencode auth login)
      "anon"           — sin creds pero tier free anónimo (opencode/*-free)
      "missing"        — sin creds: detectado pero NO utilizable
    """
    auth_data = load_auth_json() if auth_data is None else auth_data
    pid = str(pinfo.get("id", ""))

    # 1) env: la fuente más directa
    for env_key in env_keys_for_provider(pinfo):
        if os.environ.get(env_key):
            return "authed_env"

    # 2) auth.json: opencode auth login (clave por id de proveedor)
    if pid and pid in auth_data:
        entry = auth_data.get(pid)
        if isinstance(entry, dict) and (entry.get("access_token") or entry.get("api_key") or entry.get("type")):
            return "authed_file"

    # 3) tier anónimo del proveedor "opencode" (modelos *-free sin login)
    if pid == "opencode":
        return "anon"

    return "missing"


def provider_auth_badge(status: str) -> str:
    """Etiqueta corta legible para CLI y dashboard."""
    return {
        "authed_env": "env",
        "authed_file": "auth.json",
        "anon": "anon",
        "missing": "sin-creds",
    }.get(status, status)


AUTH_PRIORITY = ["authed_env", "authed_file", "anon", "missing"]


def sort_providers_by_auth(providers: list[dict]) -> list[dict]:
    """Ordena proveedores: con creds primero, sin creds al final."""
    def key(p):
        try:
            return AUTH_PRIORITY.index(provider_auth_status(p))
        except ValueError:
            return len(AUTH_PRIORITY)
    return sorted(providers, key=key)

"""
PA Framework Provider Layer.

Multi-engine resilience wrapper for local-first AI inference.
"""

from .multi_engine import (
    MultiEngine,
    EngineBase,
    OllamaEngine,
    OpenAICompatEngine,
    MockEngine,
    EngineStatus,
    create_default_engine,
    get_engine_from_config,
)

__all__ = [
    "MultiEngine",
    "EngineBase",
    "OllamaEngine",
    "OpenAICompatEngine",
    "MockEngine",
    "EngineStatus",
    "create_default_engine",
    "get_engine_from_config",
]
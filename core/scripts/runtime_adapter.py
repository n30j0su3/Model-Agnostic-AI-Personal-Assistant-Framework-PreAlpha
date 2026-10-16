#!/usr/bin/env python3
"""Minimal runtime adapter contract for optional PA runtimes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from subprocess import Popen
from typing import Any


class RuntimeAdapter(ABC):
    """Contract implemented by opt-in runtime integrations."""

    @abstractmethod
    def detect(self) -> dict[str, Any]:
        """Return installation status without changing the system."""

    @abstractmethod
    def credential_status(self) -> str:
        """Return ready, not_ready, or invalid."""

    @abstractmethod
    def spawn_chat(self, prompt: str, *, model: str, **kwargs: Any) -> Popen:
        """Start a one-shot chat subprocess."""

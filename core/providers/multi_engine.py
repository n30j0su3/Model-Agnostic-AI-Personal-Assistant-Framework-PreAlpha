"""
PA Framework Multi-Engine Provider Wrapper.

Provides resilience through multi-provider fallback routing.
Local-first design: prioritize local engines, fallback to cloud on failure.

Architecture:
    ┌─────────────────────────────────────────┐
    │            MultiEngine                  │
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
    │  │  Local  │  │  Cloud  │  │ Direct  │ │
    │  │ (Ollama)│  │(NanoGPT)│  │ (API)   │ │
    │  └─────────┘  └─────────┘  └─────────┘ │
    └─────────────────────────────────────────┘

Pattern source: local-first-ai-framework-patterns-april2026.md
"""

from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Engine Interface
# ─────────────────────────────────────────────────────────────────────────────

class EngineBase(ABC):
    """Abstract base for inference engines."""
    
    name: str = "abstract"
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """Return available model IDs."""
        pass
    
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion from messages."""
        pass
    
    @abstractmethod
    def health(self) -> bool:
        """Check engine availability."""
        pass
    
    def heartbeat(self) -> Tuple[bool, float]:
        """Return health status and latency (ms)."""
        start = time.perf_counter()
        ok = self.health()
        latency = (time.perf_counter() - start) * 1000
        return ok, latency


# ─────────────────────────────────────────────────────────────────────────────
# Mock Engines (for testing/fallback)
# ─────────────────────────────────────────────────────────────────────────────

class MockEngine(EngineBase):
    """Mock engine for testing and emergency fallback."""
    
    name = "mock"
    
    def list_models(self) -> List[str]:
        return ["mock-default"]
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        # Echo last user message
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break
        
        return {
            "model": model,
            "content": f"[MOCK] Acknowledged: {last_user[:100]}",
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
    
    def health(self) -> bool:
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Ollama Engine (Local)
# ─────────────────────────────────────────────────────────────────────────────

class OllamaEngine(EngineBase):
    """Local Ollama engine — zero cost, full privacy."""
    
    name = "ollama"
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._models_cache: List[str] = []
        self._cache_time: float = 0
        self._cache_ttl: float = 60.0  # Refresh every 60s
    
    def list_models(self) -> List[str]:
        # Cache models to avoid repeated HTTP calls
        now = time.time()
        if now - self._cache_time < self._cache_ttl and self._models_cache:
            return self._models_cache
        
        try:
            import urllib.request
            import json
            
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            req.add_header("Accept", "application/json")
            
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            
            self._models_cache = [m["name"] for m in data.get("models", [])]
            self._cache_time = now
            return self._models_cache
            
        except Exception as e:
            logger.warning(f"Ollama list_models failed: {e}")
            return self._models_cache or []
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        import urllib.request
        import json
        
        # Build request body
        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048),
            }
        }
        
        url = f"{self.base_url}/api/chat"
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        
        with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 120)) as resp:
            result = json.loads(resp.read().decode())
        
        message = result.get("message", {})
        content = message.get("content", "")
        
        # Some models (qwen3) have separate thinking field
        thinking = message.get("thinking", "")
        if thinking and not content:
            # Model is reasoning, extract final content or use thinking
            content = thinking.split("\n\n")[-1] if "\n\n" in thinking else thinking
        
        return {
            "model": model,
            "content": content,
            "thinking": thinking,  # Preserve for debugging
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
            },
        }
    
    def health(self) -> bool:
        try:
            import urllib.request
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            urllib.request.urlopen(req, timeout=3)
            return True
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI-Compatible Engine (Cloud)
# ─────────────────────────────────────────────────────────────────────────────

class OpenAICompatEngine(EngineBase):
    """OpenAI-compatible API engine (NanoGPT, OpenRouter, direct APIs)."""
    
    name = "openai_compat"
    
    # Known cloud model prefixes for routing
    CLOUD_PREFIXES = ("gpt-", "claude-", "gemini-", "openrouter/")
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.nanogpt.com/v1",
        models: List[str] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._known_models = models or [
            "gpt-4o-mini",
            "gpt-4o",
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
        ]
    
    def list_models(self) -> List[str]:
        return self._known_models
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        import urllib.request
        import json
        
        body = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        
        url = f"{self.base_url}/chat/completions"
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        
        timeout = kwargs.get("timeout", 60)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
        
        choice = result.get("choices", [{}])[0]
        return {
            "model": model,
            "content": choice.get("message", {}).get("content", ""),
            "finish_reason": choice.get("finish_reason", "stop"),
            "usage": result.get("usage", {}),
        }
    
    def health(self) -> bool:
        # For cloud APIs, we just check if key is set
        return bool(self.api_key)


# ─────────────────────────────────────────────────────────────────────────────
# MultiEngine Router
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EngineStatus:
    """Health status snapshot for an engine."""
    name: str
    healthy: bool
    latency_ms: float
    models: List[str] = field(default_factory=list)
    last_check: float = field(default_factory=time.time)


class MultiEngine:
    """
    Provider resilience wrapper — routes requests with fallback.
    
    Features:
    - Automatic model discovery from all engines
    - Local-first routing (prioritize local engines)
    - Fallback on engine failure
    - Health monitoring with latency tracking
    
    Usage:
        engine = MultiEngine([
            ("local", OllamaEngine()),
            ("cloud", OpenAICompatEngine(api_key="...")),
        ])
        
        result = engine.generate(messages, model="llama3.2")
        # Automatically routed to Ollama
        
        result = engine.generate(messages, model="gpt-4o-mini")
        # Automatically routed to cloud
    """
    
    # Cloud model prefixes for smart routing
    CLOUD_PREFIXES = ("gpt-", "claude-", "gemini-", "openrouter/", "glm-")
    
    def __init__(
        self,
        engines: List[Tuple[str, EngineBase]],
        fallback_order: List[str] = None,
        refresh_interval: float = 30.0,
    ):
        """
        Initialize MultiEngine with ordered providers.
        
        Args:
            engines: List of (name, engine) tuples
            fallback_order: Custom fallback order (default: local → cloud → mock)
            refresh_interval: Model discovery refresh interval (seconds)
        """
        self._engines = engines
        self._fallback_order = fallback_order or ["local", "cloud", "mock"]
        self._refresh_interval = refresh_interval
        
        self._model_map: Dict[str, EngineBase] = {}
        self._engine_status: Dict[str, EngineStatus] = {}
        self._last_refresh: float = 0
        
        # Always include mock as final fallback
        has_mock = any(name == "mock" for name, _ in engines)
        if not has_mock:
            self._engines.append(("mock", MockEngine()))
        
        # Initial discovery
        self._refresh_map()
    
    def _refresh_map(self) -> None:
        """Discover available models from all engines."""
        now = time.time()
        if now - self._last_refresh < self._refresh_interval:
            return
        
        self._model_map.clear()
        
        for name, engine in self._engines:
            try:
                healthy, latency = engine.heartbeat()
                models = engine.list_models() if healthy else []
                
                self._engine_status[name] = EngineStatus(
                    name=name,
                    healthy=healthy,
                    latency_ms=latency,
                    models=models,
                )
                
                # Map each model to its engine
                for model_id in models:
                    if model_id not in self._model_map:
                        self._model_map[model_id] = engine
                        
            except Exception as e:
                logger.warning(f"Engine {name} discovery failed: {e}")
                self._engine_status[name] = EngineStatus(
                    name=name,
                    healthy=False,
                    latency_ms=9999,
                    models=[],
                )
        
        self._last_refresh = now
        logger.info(f"Model map refreshed: {len(self._model_map)} models available")
    
    def _engine_for(self, model: str, retry_on_failure: bool = True) -> EngineBase:
        """
        Find engine for model with fallback logic.
        
        Routing strategy:
        1. Direct model map lookup
        2. Refresh and retry (model may be new)
        3. Cloud prefix detection → route to cloud engine
        4. Fallback chain: local → cloud → mock
        """
        # Step 1: Direct lookup
        engine = self._model_map.get(model)
        if engine and engine.health():
            return engine
        
        # Step 2: Refresh and retry
        if retry_on_failure:
            self._refresh_map()
            engine = self._model_map.get(model)
            if engine and engine.health():
                return engine
        
        # Step 3: Cloud prefix detection
        if any(model.startswith(p) for p in self.CLOUD_PREFIXES):
            for name, eng in self._engines:
                if name in ("cloud", "openai_compat") and eng.health():
                    return eng
        
        # Step 4: Fallback chain
        for name in self._fallback_order:
            for eng_name, eng in self._engines:
                if eng_name == name and eng.health():
                    logger.info(f"Using fallback engine: {name} for model {model}")
                    return eng
        
        # Final fallback: return mock (always healthy)
        for name, eng in self._engines:
            if name == "mock":
                return eng
        
        raise RuntimeError("No healthy engine available")
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion with automatic routing and fallback.
        
        Args:
            messages: Chat messages list
            model: Model ID to route
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Completion dict with content, usage, etc.
        """
        max_retries = kwargs.get("max_retries", 2)
        
        for attempt in range(max_retries + 1):
            try:
                engine = self._engine_for(model, retry_on_failure=(attempt > 0))
                return engine.generate(messages, model, **kwargs)
                
            except Exception as e:
                logger.warning(f"Generate attempt {attempt + 1} failed: {e}")
                
                if attempt == max_retries:
                    # Final fallback: mock engine
                    for name, eng in self._engines:
                        if name == "mock":
                            logger.error(f"All engines failed, using mock for {model}")
                            return eng.generate(messages, model, **kwargs)
                    
                    raise RuntimeError(f"All engines failed for model {model}: {e}")
        
        raise RuntimeError("Unexpected state in generate")
    
    def health(self) -> bool:
        """Check if at least one engine is healthy."""
        return any(status.healthy for status in self._engine_status.values())
    
    def status_report(self) -> Dict[str, Any]:
        """Return detailed status for all engines."""
        self._refresh_map()
        
        return {
            "overall_healthy": self.health(),
            "total_models": len(self._model_map),
            "engines": {
                name: {
                    "healthy": status.healthy,
                    "latency_ms": round(status.latency_ms, 2),
                    "models": status.models,
                }
                for name, status in self._engine_status.items()
            },
            "model_map_sample": list(self._model_map.keys())[:10],
        }
    
    # Convenience methods
    def list_models(self) -> List[str]:
        """Return all available models across engines."""
        self._refresh_map()
        return sorted(self._model_map.keys())
    
    def get_local_models(self) -> List[str]:
        """Return models from local engines only."""
        return [
            m for m, e in self._model_map.items()
            if getattr(e, "name", "") == "ollama"
        ]
    
    def get_cloud_models(self) -> List[str]:
        """Return models from cloud engines."""
        return [
            m for m in self._model_map.keys()
            if any(m.startswith(p) for p in self.CLOUD_PREFIXES)
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Factory Functions
# ─────────────────────────────────────────────────────────────────────────────

def create_default_engine(
    ollama_url: str = "http://localhost:11434",
    cloud_api_key: str = None,
    cloud_base_url: str = "https://api.nanogpt.com/v1",
) -> MultiEngine:
    """
    Create MultiEngine with sensible defaults.
    
    Configuration:
    - Local: Ollama (localhost:11434)
    - Cloud: OpenAI-compatible (NanoGPT or custom)
    - Fallback: Mock engine
    """
    engines = [("local", OllamaEngine(ollama_url))]
    
    if cloud_api_key:
        engines.append((
            "cloud",
            OpenAICompatEngine(api_key=cloud_api_key, base_url=cloud_base_url),
        ))
    
    return MultiEngine(engines)


def get_engine_from_config(config_path: Path = None) -> MultiEngine:
    """
    Load MultiEngine from YAML config file.
    
    Config format:
    ```yaml
    providers:
      - name: local
        type: ollama
        base_url: http://localhost:11434
      
      - name: cloud
        type: openai_compat
        api_key: ${NANOGPT_API_KEY}
        base_url: https://api.nanogpt.com/v1
        models: [gpt-4o-mini, claude-3-haiku]
    
    fallback_order: [local, cloud, mock]
    ```
    """
    if config_path is None:
        # Try JSON first (stdlib), then YAML
        config_dir = Path.home() / ".pa-framework"
        json_path = config_dir / "providers.json"
        yaml_path = config_dir / "providers.yaml"
        
        if json_path.exists():
            config_path = json_path
        elif yaml_path.exists():
            config_path = yaml_path
        else:
            logger.info(f"No config at {config_dir}, using defaults")
            return create_default_engine()
    
    if not config_path.exists():
        logger.info(f"No config at {config_path}, using defaults")
        return create_default_engine()
    
    # Load config (JSON stdlib-first, YAML fallback)
    with open(config_path) as f:
        content = f.read()
    
    if config_path.suffix == ".json":
        import json
        config = json.loads(content)
    else:
        # YAML requires pyyaml dependency
        try:
            import yaml
            config = yaml.safe_load(content)
        except ImportError:
            logger.warning("pyyaml not installed, JSON config required")
            return create_default_engine()
    
    engines = []
    for p in config.get("providers", []):
        ptype = p.get("type", "")
        name = p.get("name", ptype)
        
        if ptype == "ollama":
            engines.append((name, OllamaEngine(p.get("base_url"))))
        
        elif ptype == "openai_compat":
            api_key = p.get("api_key", "")
            # Support env var expansion
            if api_key.startswith("${") and api_key.endswith("}"):
                import os
                env_var = api_key[2:-1]
                api_key = os.environ.get(env_var, "")
            
            engines.append((
                name,
                OpenAICompatEngine(
                    api_key=api_key,
                    base_url=p.get("base_url"),
                    models=p.get("models"),
                ),
            ))
    
    fallback_order = config.get("fallback_order", ["local", "cloud", "mock"])
    return MultiEngine(engines, fallback_order=fallback_order)


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="PA MultiEngine Provider")
    parser.add_argument("--status", action="store_true", help="Show engine status")
    parser.add_argument("--models", action="store_true", help="List available models")
    parser.add_argument("--test", metavar="MODEL", help="Test generate with model")
    parser.add_argument("--api-key", metavar="KEY", help="Cloud API key for testing")
    
    args = parser.parse_args()
    
    engine = create_default_engine(
        cloud_api_key=args.api_key or "",
    )
    
    if args.status:
        report = engine.status_report()
        print(json.dumps(report, indent=2))
    
    elif args.models:
        models = engine.list_models()
        print(json.dumps({"models": models, "count": len(models)}, indent=2))
    
    elif args.test:
        test_messages = [
            {"role": "user", "content": "Say 'PA Framework online' in exactly those words."}
        ]
        
        try:
            result = engine.generate(test_messages, args.test)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2))
    
    else:
        # Default: show quick status
        print(json.dumps(engine.status_report(), indent=2))
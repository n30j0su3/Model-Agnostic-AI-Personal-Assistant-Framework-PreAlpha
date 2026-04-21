"""
PA Framework TOML Skill Executor.

Declarative skills with template interpolation — portable, readable, versionable.

Architecture:
    ┌─────────────────────────────────────────┐
    │         Skill Executor                  │
    │  ┌───────────────────────────────────┐  │
    │  │  TOML Manifest → SkillManifest    │  │
    │  │  Steps → Tool Calls               │  │
    │  │  Context → Interpolation          │  │
    │  └───────────────────────────────────┘  │
    └─────────────────────────────────────────┘

Pattern source: local-first-ai-framework-patterns-april2026.md
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Skill Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(slots=True)
class SkillStep:
    """Single step in a skill workflow."""
    tool_name: str
    arguments_template: str = "{}"
    output_key: str = ""
    description: str = ""
    retry_count: int = 0
    retry_delay: float = 1.0


@dataclass
class SkillManifest:
    """Declarative skill definition from TOML."""
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    steps: List[SkillStep] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Validate required capabilities
        for cap in self.required_capabilities:
            if not isinstance(cap, str):
                raise ValueError(f"Capability must be string: {cap}")
    
    def __repr__(self) -> str:
        return f"SkillManifest({self.name} v{self.version}, {len(self.steps)} steps)"


# ─────────────────────────────────────────────────────────────────────────────
# Tool Protocol
# ─────────────────────────────────────────────────────────────────────────────

class ToolProtocol(Protocol):
    """Protocol for tools that can be invoked by skills."""
    
    name: str
    
    def invoke(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with given arguments."""
        ...


class ToolRegistry:
    """
    Registry for tools available to skill executor.
    
    Supports:
    - Callable functions
    - Protocol-compliant objects
    - Mock tools for testing
    """
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._mock_results: Dict[str, Any] = {}
    
    def register(self, name: str, tool: Callable | ToolProtocol) -> None:
        """Register a tool by name."""
        self._tools[name] = tool
        logger.debug(f"Tool registered: {name}")
    
    def get(self, name: str) -> Optional[Callable]:
        """Get tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return sorted(self._tools.keys())
    
    def set_mock_result(self, tool_name: str, result: Any) -> None:
        """Set mock result for testing."""
        self._mock_results[tool_name] = result
    
    def invoke(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke tool with arguments.
        
        Args:
            name: Tool name
            arguments: Tool arguments dict
        
        Returns:
            Tool result dict
        """
        # Check for mock result first (testing mode)
        if name in self._mock_results:
            return self._mock_results[name]
        
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Tool not found: {name}")
        
        try:
            # Support both callable and protocol
            if hasattr(tool, "invoke"):
                result = tool.invoke(arguments)
            else:
                result = tool(**arguments)
            
            # Normalize result to dict
            if isinstance(result, dict):
                return result
            return {"result": result, "success": True}
            
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return {"error": str(e), "success": False}


class ToolNotFoundError(Exception):
    """Raised when tool is not in registry."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Skill Loader
# ─────────────────────────────────────────────────────────────────────────────

def load_skill(path: Union[Path, str]) -> SkillManifest:
    """Load a skill manifest from a TOML file.
    
    Args:
        path: Path to the TOML skill file (Path or str)
        
    Returns:
        SkillManifest instance
        
    Raises:
        FileNotFoundError: If skill file doesn't exist
        ValueError: If TOML is malformed or missing required fields
    """
    path = Path(path) if isinstance(path, str) else path
    if not path.exists():
        raise FileNotFoundError(f"Skill file not found: {path}")
    
    with open(path, "rb") as f:
        data = tomllib.load(f)
    
    skill_data = data.get("skill", {})
    
    # Parse steps (TOML [[steps]] arrays are at root level, not nested in [skill])
    steps = []
    steps_data = data.get("steps", [])
    for step_data in steps_data:
        # TOML uses 'tool' field, parser expects 'tool_name'
        tool_name = step_data.get("tool", step_data.get("tool_name", ""))
        # TOML may have 'prompt' field for generate steps
        prompt_template = step_data.get("prompt", step_data.get("arguments_template", "{}"))
        
        step = SkillStep(
            tool_name=tool_name,
            arguments_template=prompt_template,
            output_key=step_data.get("output_key", ""),
            description=step_data.get("description", ""),
            retry_count=step_data.get("retry_count", step_data.get("max_retries", 0)),
            retry_delay=step_data.get("retry_delay", 1.0),
        )
        # For generate-type steps, tool_name can be empty (uses model inference)
        if step.tool_name or step_data.get("type") == "generate":
            steps.append(step)
        elif not step.tool_name:
            raise ValueError(f"Step missing 'tool' or 'tool_name' field in {path}")
    
    return SkillManifest(
        name=skill_data.get("name", path.stem),
        version=skill_data.get("version", "0.1.0"),
        description=skill_data.get("description", ""),
        author=skill_data.get("author", ""),
        steps=steps,
        required_capabilities=skill_data.get("required_capabilities", []),
        metadata=skill_data.get("metadata", {}),
    )


def discover_skills(directory: Union[Path, str]) -> List[SkillManifest]:
    """
    Discover all TOML skill files in directory.
    
    Args:
        directory: Directory to scan (Path or str)
    
    Returns:
        List of SkillManifest objects
    """
    directory = Path(directory) if isinstance(directory, str) else directory
    if not directory.exists():
        logger.warning(f"Skill directory not found: {directory}")
        return []
    
    skills = []
    for toml_file in sorted(directory.glob("*.toml")):
        try:
            skill = load_skill(toml_file)
            skills.append(skill)
            logger.debug(f"Loaded skill: {skill.name}")
        except Exception as e:
            logger.warning(f"Failed to load {toml_file}: {e}")
    
    return skills


# ─────────────────────────────────────────────────────────────────────────────
# Skill Executor
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExecutionResult:
    """Result of skill execution."""
    skill_name: str
    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    steps_completed: int = 0
    total_steps: int = 0
    duration_ms: float = 0.0


class SkillExecutor:
    """
    Execute skill steps with context accumulation.
    
    Features:
    - Template interpolation with context variables
    - Output key extraction for step chaining
    - Retry logic per step
    - Error recovery and reporting
    
    Usage:
        registry = ToolRegistry()
        registry.register("web_search", web_search_fn)
        
        executor = SkillExecutor(registry)
        skill = load_skill("research.toml")
        
        result = executor.execute(skill, {"query": "AI frameworks"})
        # result.outputs contains all step outputs
    """
    
    def __init__(self, tool_registry: ToolRegistry = None, registry: ToolRegistry = None):
        # Accept both arg names for flexibility
        self._tools = tool_registry or registry or ToolRegistry()
    
    def _interpolate(self, template: str, context: Dict[str, Any]) -> str:
        """
        Interpolate template string with context variables.
        
        Supports:
        - {variable} → simple replacement
        - {nested.key} → nested access (not yet implemented)
        
        Args:
            template: Template string with {var} placeholders
            context: Context dict for interpolation
        
        Returns:
            Interpolated string
        """
        result = template
        
        # Find all {var} patterns
        pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
        matches = re.findall(pattern, template)
        
        for var_name in matches:
            if var_name in context:
                value = context[var_name]
                # Convert to JSON-safe string
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                result = result.replace(f"{{{var_name}}}", value_str)
            else:
                logger.warning(f"Missing context variable: {var_name}")
        
        return result
    
    def execute(
        self,
        skill: SkillManifest,
        inputs: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        dry_run: bool = False,
    ) -> ExecutionResult:
        """
        Execute skill workflow step by step.
        
        Args:
            skill: SkillManifest to execute
            inputs: Initial input context (alias: context)
            context: Alternative arg name for inputs
            dry_run: If True, skip actual tool invocation
            
        Returns:
            ExecutionResult with outputs and status
        """
        import time
        
        # Accept both arg names
        initial_context = inputs or context or {}
        start_time = time.perf_counter()
        
        # Initialize context with inputs
        context = initial_context.copy()
        outputs: Dict[str, Any] = {}
        errors: List[str] = []
        steps_completed = 0
        
        logger.info(f"Executing skill: {skill.name} ({len(skill.steps)} steps)")
        
        for i, step in enumerate(skill.steps):
            logger.debug(f"Step {i + 1}: {step.tool_name}")
            
            try:
                # Interpolate arguments template
                args_json = self._interpolate(step.arguments_template, context)
                arguments = json.loads(args_json)
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would call {step.tool_name} with {arguments}")
                    outputs[step.output_key or f"step_{i}"] = {"dry_run": True}
                    steps_completed += 1
                    continue
                
                # Invoke tool (with retry logic)
                result = self._invoke_with_retry(step, arguments)
                
                # Update context for next steps
                if step.output_key:
                    context[step.output_key] = result
                    outputs[step.output_key] = result
                else:
                    context[f"step_{i}_result"] = result
                
                steps_completed += 1
                
            except json.JSONDecodeError as e:
                err = f"Step {i + 1}: JSON decode error - {e}"
                errors.append(err)
                logger.error(err)
                break
                
            except ToolNotFoundError as e:
                err = f"Step {i + 1}: Tool not found - {e}"
                errors.append(err)
                logger.error(err)
                break
                
            except Exception as e:
                err = f"Step {i + 1}: {e}"
                errors.append(err)
                logger.error(err)
                # Continue execution despite errors (configurable)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        return ExecutionResult(
            skill_name=skill.name,
            success=len(errors) == 0,
            outputs=outputs,
            errors=errors,
            steps_completed=steps_completed,
            total_steps=len(skill.steps),
            duration_ms=round(duration_ms, 2),
        )
    
    def _invoke_with_retry(
        self,
        step: SkillStep,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Invoke tool with retry logic.
        
        Args:
            step: SkillStep with retry config
            arguments: Tool arguments
        
        Returns:
            Tool result dict
        """
        import time
        
        max_retries = step.retry_count
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self._tools.invoke(step.tool_name, arguments)
                
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        f"Tool {step.tool_name} failed (attempt {attempt + 1}), "
                        f"retrying in {step.retry_delay}s"
                    )
                    time.sleep(step.retry_delay)
        
        raise RuntimeError(f"Tool {step.tool_name} failed after {max_retries} retries: {last_error}")


# ─────────────────────────────────────────────────────────────────────────────
# Built-in Mock Tools
# ─────────────────────────────────────────────────────────────────────────────

def mock_think(thought: str = "", **kwargs) -> Dict[str, Any]:
    """Mock think tool for testing."""
    return {"summary": f"[MOCK] Thought processed: {thought[:100]}", "success": True}


def mock_web_search(query: str = "", **kwargs) -> Dict[str, Any]:
    """Mock web search for testing."""
    return {
        "results": [
            {"title": f"Result 1 for {query}", "url": "https://example.com/1"},
            {"title": f"Result 2 for {query}", "url": "https://example.com/2"},
        ],
        "success": True,
    }


def create_mock_registry() -> ToolRegistry:
    """Create registry with mock tools for testing."""
    registry = ToolRegistry()
    registry.register("web_search", mock_web_search)
    registry.register("think", mock_think)
    registry.register("llm", lambda **kwargs: {"response": "[MOCK] LLM response", "success": True})
    return registry


# ─────────────────────────────────────────────────────────────────────────────
# Example Skill TOML
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_SKILL_TOML = """
# skills/research_and_summarize.toml
[skill]
name = "research_and_summarize"
version = "0.1.0"
description = "Search web and summarize results"
author = "pa-framework"
required_capabilities = ["network:fetch"]

[[steps]]
tool_name = "web_search"
arguments_template = '{"query": "{query}"}'
output_key = "search_results"
description = "Search for relevant results"

[[steps]]
tool_name = "think"
arguments_template = '{"thought": "Summarize findings: {search_results}"}'
output_key = "summary"
description = "Process and summarize"

[[steps]]
tool_name = "llm"
arguments_template = '{"prompt": "Based on {summary}, provide key insights"}'
output_key = "insights"
"""


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import tempfile
    
    parser = argparse.ArgumentParser(description="PA TOML Skill Executor")
    parser.add_argument("--demo", action="store_true", help="Run demo skill")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no tool calls)")
    parser.add_argument("--list", metavar="DIR", help="List skills in directory")
    parser.add_argument("--run", metavar="TOML", help="Run specific skill file")
    parser.add_argument("--inputs", metavar="JSON", help="Input context as JSON")
    
    args = parser.parse_args()
    
    registry = create_mock_registry()
    executor = SkillExecutor(registry)
    
    if args.demo:
        # Create temp skill file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(EXAMPLE_SKILL_TOML)
            temp_path = Path(f.name)
        
        skill = load_skill(temp_path)
        print(f"Loaded: {skill}")
        
        result = executor.execute(skill, {"query": "AI frameworks 2026"}, dry_run=args.dry_run)
        print(json.dumps({
            "skill": result.skill_name,
            "success": result.success,
            "outputs": result.outputs,
            "errors": result.errors,
            "steps": f"{result.steps_completed}/{result.total_steps}",
            "duration_ms": result.duration_ms,
        }, indent=2))
        
        temp_path.unlink()
    
    elif args.list:
        skills_dir = Path(args.list)
        skills = discover_skills(skills_dir)
        print(json.dumps({
            "directory": str(skills_dir),
            "skills_found": len(skills),
            "skills": [{"name": s.name, "steps": len(s.steps)} for s in skills],
        }, indent=2))
    
    elif args.run:
        skill_path = Path(args.run)
        skill = load_skill(skill_path)
        
        inputs = {}
        if args.inputs:
            inputs = json.loads(args.inputs)
        
        result = executor.execute(skill, inputs, dry_run=args.dry_run)
        print(json.dumps({
            "skill": result.skill_name,
            "success": result.success,
            "outputs": result.outputs,
            "errors": result.errors,
            "duration_ms": result.duration_ms,
        }, indent=2))
    
    else:
        parser.print_help()
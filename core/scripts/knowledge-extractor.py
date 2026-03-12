#!/usr/bin/env python3
"""
PA Framework - Knowledge Extractor Module
Dual output system (JSON + MD) for knowledge extraction from sessions.

Part of Session-End Pipeline

Usage:
    from knowledge_extractor import KnowledgeExtractor

    extractor = KnowledgeExtractor()
    results = extractor.extract_all_knowledge(session_file)

Configuration (config/framework.yaml):
    knowledge_extraction:
      enabled: true
      auto_detect:
        discoveries: true
        prompts: true
        ideas: true
        best_practices: true
      tags:
        discovery: "#discovery"
        prompt_success: "#prompt-success"
        idea: "#idea"
        best_practice: "#best-practice"
      output:
        discoveries: "core/.context/knowledge/learning/discoveries.md"
        prompts: "core/.context/knowledge/prompts/registry.json"
        ideas: "core/.context/codebase/ideas.md"
        best_practices: "core/.context/knowledge/learning/best-practices.md"
        index: "core/.context/knowledge/knowledge-index.json"
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32" and sys.stdout.isatty():
    try:
        import io

        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except (ValueError, AttributeError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
CONFIG_FILE = REPO_ROOT / "config" / "framework.yaml"

DEFAULT_CONFIG = {
    "enabled": True,
    "auto_detect": {
        "discoveries": True,
        "prompts": True,
        "ideas": True,
        "best_practices": True,
    },
    "tags": {
        "discovery": "#discovery",
        "prompt_success": "#prompt-success",
        "idea": "#idea",
        "best_practice": "#best-practice",
    },
    "output": {
        "discoveries": "core/.context/knowledge/learning/discoveries.md",
        "prompts": "core/.context/knowledge/prompts/registry.json",
        "ideas": "core/.context/codebase/ideas.md",
        "best_practices": "core/.context/knowledge/learning/best-practices.md",
        "index": "core/.context/knowledge/knowledge-index.json",
    },
}


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.END}"


def safe_print(text: str, **kwargs):
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding)
        print(safe_text, **kwargs)


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dictionary with configuration data.
    """
    try:
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return _parse_yaml_simple(config_path)
    except FileNotFoundError:
        return {}


def _parse_yaml_simple(config_path: Path) -> Dict[str, Any]:
    """
    Simple YAML parser for basic key-value pairs.

    Args:
        config_path: Path to the YAML file.

    Returns:
        Dictionary with parsed configuration.
    """
    config: Dict[str, Any] = {}
    try:
        content = config_path.read_text(encoding="utf-8")
        current_section = None
        current_subsection = None

        for line in content.split("\n"):
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("  ") and current_section:
                if line.startswith("    "):
                    if current_subsection:
                        key_match = re.match(r"\s{4}(\w+):\s*(.+)", line)
                        if key_match:
                            key, value = key_match.groups()
                            value = value.strip().strip('"').strip("'")
                            if value.lower() == "true":
                                value = True
                            elif value.lower() == "false":
                                value = False
                            config[current_section][current_subsection][key] = value
                else:
                    key_match = re.match(r"\s{2}(\w+):\s*(.+)?", line)
                    if key_match:
                        key, value = key_match.groups()
                        if value is None:
                            config[current_section][key] = {}
                            current_subsection = key
                        else:
                            value = value.strip().strip('"').strip("'")
                            if value.lower() == "true":
                                value = True
                            elif value.lower() == "false":
                                value = False
                            config[current_section][key] = value
                            current_subsection = None
            elif ":" in line:
                key = line.split(":")[0].strip()
                config[key] = {}
                current_section = key
                current_subsection = None
    except Exception:
        pass

    return config


class KnowledgeExtractor:
    """
    Dual output system for knowledge extraction from session files.

    Extracts discoveries, successful prompts, validated ideas, and best
    practices from session markdown files, outputting to both JSON index
    and Markdown files.

    Attributes:
        config: Configuration dictionary
        discoveries_file: Path to discoveries markdown file
        prompts_file: Path to prompts registry JSON file
        ideas_file: Path to ideas markdown file
        best_practices_file: Path to best practices markdown file
        index_file: Path to knowledge index JSON file
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize KnowledgeExtractor with configuration.

        Args:
            config: Optional configuration dictionary. If None, loads from
                   config/framework.yaml with fallback to defaults.
        """
        self.config = self._load_config(config)
        self._setup_paths()
        self._ensure_directories()
        self._ensure_files()

    def _load_config(self, config: Optional[Dict]) -> Dict:
        """
        Load and merge configuration.

        Args:
            config: Optional provided configuration.

        Returns:
            Merged configuration dictionary.
        """
        if config:
            return {**DEFAULT_CONFIG, **config}

        yaml_config = load_yaml_config(CONFIG_FILE)
        extraction_config = yaml_config.get("knowledge_extraction", {})

        merged = {**DEFAULT_CONFIG}
        for key in ["enabled", "auto_detect", "tags", "output"]:
            if key in extraction_config:
                if isinstance(merged[key], dict):
                    merged[key] = {**merged[key], **extraction_config[key]}
                else:
                    merged[key] = extraction_config[key]

        return merged

    def _setup_paths(self) -> None:
        """Setup file paths from configuration."""
        output_config = self.config.get("output", DEFAULT_CONFIG["output"])

        self.discoveries_file = REPO_ROOT / output_config.get(
            "discoveries", DEFAULT_CONFIG["output"]["discoveries"]
        )
        self.prompts_file = REPO_ROOT / output_config.get(
            "prompts", DEFAULT_CONFIG["output"]["prompts"]
        )
        self.ideas_file = REPO_ROOT / output_config.get(
            "ideas", DEFAULT_CONFIG["output"]["ideas"]
        )
        self.best_practices_file = REPO_ROOT / output_config.get(
            "best_practices", DEFAULT_CONFIG["output"]["best_practices"]
        )
        self.index_file = REPO_ROOT / output_config.get(
            "index", DEFAULT_CONFIG["output"]["index"]
        )

    def _ensure_directories(self) -> None:
        """Create directory structure if it doesn't exist."""
        for file_path in [
            self.discoveries_file,
            self.prompts_file,
            self.ideas_file,
            self.best_practices_file,
            self.index_file,
        ]:
            file_path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_files(self) -> None:
        """Initialize output files if they don't exist."""
        if not self.discoveries_file.exists():
            self._write_md_header(
                self.discoveries_file,
                "Discoveries Log",
                "Auto-generated discoveries log for PA Framework",
            )

        if not self.prompts_file.exists():
            self._write_json(self.prompts_file, {"prompts": [], "last_updated": None})

        if not self.ideas_file.exists():
            self._write_md_header(
                self.ideas_file,
                "Ideas Log",
                "Auto-generated ideas log for PA Framework",
            )

        if not self.best_practices_file.exists():
            self._write_md_header(
                self.best_practices_file,
                "Best Practices Log",
                "Auto-generated best practices log for PA Framework",
            )

        if not self.index_file.exists():
            self._write_json(
                self.index_file,
                {
                    "discoveries": 0,
                    "prompts": 0,
                    "ideas": 0,
                    "best_practices": 0,
                    "last_extraction": None,
                    "history": [],
                },
            )

    def _write_md_header(self, file_path: Path, title: str, description: str) -> None:
        """
        Write markdown file header.

        Args:
            file_path: Path to write the file.
            title: Title for the document.
            description: Description text.
        """
        header = f"""# {title}

> {description}
> Part of Knowledge Extraction System

---

"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(header)
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to write header: {e}", Colors.RED))

    def _write_json(self, file_path: Path, data: Dict) -> None:
        """
        Write data to JSON file.

        Args:
            file_path: Path to write the file.
            data: Dictionary to write.
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to write JSON: {e}", Colors.RED))

    def _read_json(self, file_path: Path) -> Dict:
        """
        Read data from JSON file.

        Args:
            file_path: Path to read from.

        Returns:
            Dictionary with file contents or empty dict on error.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _append_to_md(self, file_path: Path, content: str) -> bool:
        """
        Append content to markdown file.

        Args:
            file_path: Path to the markdown file.
            content: Content to append.

        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to append to MD: {e}", Colors.RED))
            return False

    def _get_tag(self, tag_name: str) -> str:
        """
        Get tag string from configuration.

        Args:
            tag_name: Name of the tag.

        Returns:
            Tag string.
        """
        tags = self.config.get("tags", DEFAULT_CONFIG["tags"])
        return tags.get(tag_name, DEFAULT_CONFIG["tags"].get(tag_name, ""))

    def _is_auto_detect_enabled(self, category: str) -> bool:
        """
        Check if auto-detection is enabled for a category.

        Args:
            category: Category name to check.

        Returns:
            True if auto-detection is enabled.
        """
        auto_detect = self.config.get("auto_detect", DEFAULT_CONFIG["auto_detect"])
        return auto_detect.get(category, True)

    def _find_line_number(self, content: str, search_text: str) -> int:
        """
        Find the line number of text in content.

        Args:
            content: Full content to search.
            search_text: Text to find.

        Returns:
            Line number (1-indexed) or 0 if not found.
        """
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 0

    def extract_session_discoveries(self, session_file: Path) -> List[Dict]:
        """
        Extract discoveries from session file.

        Auto-detection:
        - Sections with "## Hallazgos" or "## Discoveries"
        - Blocks containing "descubrimiento" or "discovery"

        Manual tags: #discovery

        Args:
            session_file: Path to the session markdown file.

        Returns:
            List of dicts with:
            - title, context, discovery, impact
            - extracted_from (line number)
            - status: "pending_validation"
            - auto_detected: bool
        """
        discoveries: List[Dict] = []
        tag = self._get_tag("discovery")
        auto_enabled = self._is_auto_detect_enabled("discoveries")

        try:
            content = session_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if tag and tag in line:
                    discovery = self._parse_tagged_discovery(lines, i)
                    if discovery:
                        discoveries.append(discovery)
                    continue

                if auto_enabled:
                    if re.match(r"^##\s+(Hallazgos|Discoveries)", line, re.IGNORECASE):
                        section_discoveries = self._parse_discovery_section(
                            lines, i + 1
                        )
                        discoveries.extend(section_discoveries)

                    if (
                        "descubrimiento:" in line.lower()
                        or "discovery:" in line.lower()
                    ):
                        discovery = self._parse_inline_discovery(lines, i)
                        if discovery:
                            discoveries.append(discovery)

        except Exception as e:
            safe_print(c(f"[WARN] Error extracting discoveries: {e}", Colors.YELLOW))

        return discoveries

    def _parse_tagged_discovery(
        self, lines: List[str], start_idx: int
    ) -> Optional[Dict]:
        """
        Parse a discovery marked with #discovery tag.

        Args:
            lines: List of lines from the file.
            start_idx: Index of the tagged line.

        Returns:
            Discovery dictionary or None.
        """
        context_lines = []
        discovery_text = ""
        impact_text = ""

        for i in range(max(0, start_idx - 3), start_idx):
            context_lines.append(lines[i].strip())

        current_block = []
        for i in range(start_idx, min(len(lines), start_idx + 10)):
            line = lines[i].strip()
            if line.startswith("#") and i > start_idx:
                break
            current_block.append(line)

        discovery_text = " ".join(current_block)
        discovery_text = discovery_text.replace(self._get_tag("discovery"), "").strip()

        title_match = re.match(r"\*\*(.+?)\*\*[:\s-]*(.*)", discovery_text)
        if title_match:
            title = title_match.group(1).strip()
            discovery_text = title_match.group(2).strip()
        else:
            title = (
                discovery_text[:50] + "..."
                if len(discovery_text) > 50
                else discovery_text
            )

        return {
            "title": title,
            "context": " ".join(context_lines)[:200],
            "discovery": discovery_text,
            "impact": "To be evaluated",
            "extracted_from": start_idx + 1,
            "status": "pending_validation",
            "auto_detected": False,
            "timestamp": datetime.now().isoformat(),
        }

    def _parse_discovery_section(self, lines: List[str], start_idx: int) -> List[Dict]:
        """
        Parse a Hallazgos/Discoveries section.

        Args:
            lines: List of lines from the file.
            start_idx: Index after the section header.

        Returns:
            List of discovery dictionaries.
        """
        discoveries = []
        current_item: List[str] = []

        for i in range(start_idx, len(lines)):
            line = lines[i]
            if line.startswith("## "):
                break
            if line.strip().startswith(("-", "*", "1.", "2.", "3.")):
                if current_item:
                    discovery = self._create_discovery_from_block(current_item, i)
                    if discovery:
                        discoveries.append(discovery)
                current_item = [line]
            elif current_item:
                current_item.append(line)

        if current_item:
            discovery = self._create_discovery_from_block(current_item, len(lines))
            if discovery:
                discoveries.append(discovery)

        return discoveries

    def _create_discovery_from_block(
        self, block: List[str], line_num: int
    ) -> Optional[Dict]:
        """
        Create discovery dict from text block.

        Args:
            block: List of lines in the block.
            line_num: Line number for reference.

        Returns:
            Discovery dictionary or None.
        """
        text = " ".join(line.strip() for line in block if line.strip())
        text = re.sub(r"^[-*\d.]+\s*", "", text)

        if not text:
            return None

        return {
            "title": text[:80],
            "context": "Auto-detected from session",
            "discovery": text,
            "impact": "To be evaluated",
            "extracted_from": line_num,
            "status": "pending_validation",
            "auto_detected": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _parse_inline_discovery(self, lines: List[str], idx: int) -> Optional[Dict]:
        """
        Parse an inline discovery statement.

        Args:
            lines: List of lines from the file.
            idx: Index of the line containing discovery.

        Returns:
            Discovery dictionary or None.
        """
        line = lines[idx]
        match = re.search(
            r"(?:descubrimiento|discovery)[:\s]+(.+)", line, re.IGNORECASE
        )
        if match:
            discovery_text = match.group(1).strip()
            return {
                "title": discovery_text[:80],
                "context": "Auto-detected from inline text",
                "discovery": discovery_text,
                "impact": "To be evaluated",
                "extracted_from": idx + 1,
                "status": "pending_validation",
                "auto_detected": True,
                "timestamp": datetime.now().isoformat(),
            }
        return None

    def extract_successful_prompts(self, session_file: Path) -> List[Dict]:
        """
        Extract successful prompts from session file.

        Auto-detection:
        - Code blocks followed by "funciono", "exitoso", "success"

        Manual tags: #prompt-success

        Args:
            session_file: Path to the session markdown file.

        Returns:
            List of dicts with:
            - id, category, prompt_template
            - extracted_from, status, auto_detected
        """
        prompts: List[Dict] = []
        tag = self._get_tag("prompt_success")
        auto_enabled = self._is_auto_detect_enabled("prompts")

        try:
            content = session_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            code_block_start = None
            code_block_content: List[str] = []

            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    if code_block_start is None:
                        code_block_start = i
                        code_block_content = []
                    else:
                        if auto_enabled and i + 1 < len(lines):
                            next_lines = " ".join(
                                lines[i + 1 : min(i + 4, len(lines))]
                            ).lower()
                            success_indicators = [
                                "funciono",
                                "funciono",
                                "exitoso",
                                "exito",
                                "success",
                                "[ok]",
                                "correcto",
                                "resolved",
                                "solved",
                            ]
                            if any(ind in next_lines for ind in success_indicators):
                                prompt = self._create_prompt_from_code_block(
                                    code_block_content, code_block_start
                                )
                                if prompt:
                                    prompts.append(prompt)

                        code_block_start = None
                        code_block_content = []
                elif code_block_start is not None:
                    code_block_content.append(line)

                if tag and tag in line:
                    prompt = self._parse_tagged_prompt(lines, i)
                    if prompt:
                        prompts.append(prompt)

        except Exception as e:
            safe_print(c(f"[WARN] Error extracting prompts: {e}", Colors.YELLOW))

        return prompts

    def _create_prompt_from_code_block(
        self, code_lines: List[str], start_idx: int
    ) -> Optional[Dict]:
        """
        Create prompt dict from code block.

        Args:
            code_lines: Lines within the code block.
            start_idx: Starting line index.

        Returns:
            Prompt dictionary or None.
        """
        content = "\n".join(code_lines).strip()
        if not content:
            return None

        prompt_id = f"PROMPT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(content) % 10000:04d}"

        return {
            "id": prompt_id,
            "category": self._categorize_prompt(content),
            "prompt_template": content,
            "extracted_from": start_idx + 1,
            "status": "validated",
            "auto_detected": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _categorize_prompt(self, content: str) -> str:
        """
        Categorize prompt based on content.

        Args:
            content: Prompt content.

        Returns:
            Category string.
        """
        content_lower = content.lower()

        if (
            "python" in content_lower
            or "def " in content_lower
            or "import " in content_lower
        ):
            return "python"
        if (
            "bash" in content_lower
            or "npm " in content_lower
            or "git " in content_lower
        ):
            return "bash"
        if (
            "javascript" in content_lower
            or "function " in content_lower
            or "const " in content_lower
        ):
            return "javascript"
        if "sql" in content_lower or "select " in content_lower:
            return "sql"
        if "yaml" in content_lower or "json" in content_lower:
            return "config"

        return "general"

    def _parse_tagged_prompt(self, lines: List[str], idx: int) -> Optional[Dict]:
        """
        Parse a prompt marked with #prompt-success tag.

        Args:
            lines: List of lines from the file.
            idx: Index of the tagged line.

        Returns:
            Prompt dictionary or None.
        """
        prompt_lines = []
        for i in range(max(0, idx - 10), min(len(lines), idx + 5)):
            if lines[i].strip().startswith("```"):
                if i < idx:
                    continue
                else:
                    break
            if i <= idx or lines[i].strip().startswith("```"):
                prompt_lines.append(lines[i])

        content = "\n".join(prompt_lines).strip()
        content = content.replace(self._get_tag("prompt_success"), "").strip()

        if not content:
            return None

        prompt_id = f"PROMPT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(content) % 10000:04d}"

        return {
            "id": prompt_id,
            "category": self._categorize_prompt(content),
            "prompt_template": content,
            "extracted_from": idx + 1,
            "status": "validated",
            "auto_detected": False,
            "timestamp": datetime.now().isoformat(),
        }

    def extract_validated_ideas(self, session_file: Path) -> List[Dict]:
        """
        Extract validated ideas from session file.

        Auto-detection:
        - Items with "[OK]", "validado", "aprobado", "approved"
        - Sections with "## Ideas"

        Manual tags: #idea

        Args:
            session_file: Path to the session markdown file.

        Returns:
            List of dicts with:
            - title, description, priority
            - extracted_from, status, auto_detected
        """
        ideas: List[Dict] = []
        tag = self._get_tag("idea")
        auto_enabled = self._is_auto_detect_enabled("ideas")

        try:
            content = session_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            in_ideas_section = False

            for i, line in enumerate(lines):
                if line.startswith("## Ideas"):
                    in_ideas_section = True
                    continue
                if line.startswith("## ") and in_ideas_section:
                    in_ideas_section = False

                if tag and tag in line:
                    idea = self._parse_tagged_idea(lines, i)
                    if idea:
                        ideas.append(idea)
                    continue

                if auto_enabled:
                    validation_indicators = [
                        "[ok]",
                        "validado",
                        "aprobado",
                        "approved",
                        "aceptado",
                        "confirmado",
                    ]
                    line_lower = line.lower()

                    if any(ind in line_lower for ind in validation_indicators):
                        if line.strip().startswith(("-", "*", "1.", "2.", "3.")):
                            idea = self._parse_validated_item(line, i)
                            if idea:
                                ideas.append(idea)

                    if in_ideas_section and line.strip().startswith(("-", "*")):
                        if re.match(r"^[-*]\s*\[x\]", line, re.IGNORECASE):
                            idea = self._parse_checked_idea(line, i)
                            if idea:
                                ideas.append(idea)

        except Exception as e:
            safe_print(c(f"[WARN] Error extracting ideas: {e}", Colors.YELLOW))

        return ideas

    def _parse_tagged_idea(self, lines: List[str], idx: int) -> Optional[Dict]:
        """
        Parse an idea marked with #idea tag.

        Args:
            lines: List of lines from the file.
            idx: Index of the tagged line.

        Returns:
            Idea dictionary or None.
        """
        line = lines[idx]
        text = line.replace(self._get_tag("idea"), "").strip()
        text = re.sub(r"^[-*\d.]+\s*", "", text)

        if not text:
            return None

        return {
            "title": text[:100],
            "description": text,
            "priority": "medium",
            "extracted_from": idx + 1,
            "status": "pending",
            "auto_detected": False,
            "timestamp": datetime.now().isoformat(),
        }

    def _parse_validated_item(self, line: str, idx: int) -> Optional[Dict]:
        """
        Parse a validated item from a list line.

        Args:
            line: The line containing the validated item.
            idx: Line index.

        Returns:
            Idea dictionary or None.
        """
        text = re.sub(r"^[-*\d.]+\s*", "", line.strip())
        text = re.sub(r"\[ok\]|\[x\]", "", text, flags=re.IGNORECASE).strip()

        if not text:
            return None

        return {
            "title": text[:100],
            "description": text,
            "priority": "high",
            "extracted_from": idx + 1,
            "status": "validated",
            "auto_detected": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _parse_checked_idea(self, line: str, idx: int) -> Optional[Dict]:
        """
        Parse a checked idea from Ideas section.

        Args:
            line: The line containing the checked idea.
            idx: Line index.

        Returns:
            Idea dictionary or None.
        """
        text = re.sub(r"^[-*]\s*\[x\]\s*", "", line.strip(), flags=re.IGNORECASE)

        if not text:
            return None

        return {
            "title": text[:100],
            "description": text,
            "priority": "medium",
            "extracted_from": idx + 1,
            "status": "validated",
            "auto_detected": True,
            "timestamp": datetime.now().isoformat(),
        }

    def extract_best_practices(self, session_file: Path) -> List[Dict]:
        """
        Extract best practices from session file.

        Auto-detection:
        - Sections with "## Solucion" followed by successful resolution
        - Patterns that worked

        Manual tags: #best-practice

        Args:
            session_file: Path to the session markdown file.

        Returns:
            List of dicts with:
            - title, context, practice, benefit
            - extracted_from, status, auto_detected
        """
        practices: List[Dict] = []
        tag = self._get_tag("best_practice")
        auto_enabled = self._is_auto_detect_enabled("best_practices")

        try:
            content = session_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if tag and tag in line:
                    practice = self._parse_tagged_practice(lines, i)
                    if practice:
                        practices.append(practice)
                    continue

                if auto_enabled:
                    if re.match(r"^##\s+Soluci[oó]n", line, re.IGNORECASE):
                        practice = self._parse_solution_section(lines, i)
                        if practice:
                            practices.append(practice)

                    if (
                        "funciono" in line.lower()
                        or "worked" in line.lower()
                        or "resolved" in line.lower()
                    ):
                        if i > 0 and "```" in lines[i - 1]:
                            practice = self._parse_code_solution(lines, i)
                            if practice:
                                practices.append(practice)

        except Exception as e:
            safe_print(c(f"[WARN] Error extracting best practices: {e}", Colors.YELLOW))

        return practices

    def _parse_tagged_practice(self, lines: List[str], idx: int) -> Optional[Dict]:
        """
        Parse a best practice marked with #best-practice tag.

        Args:
            lines: List of lines from the file.
            idx: Index of the tagged line.

        Returns:
            Practice dictionary or None.
        """
        context_lines = []
        for i in range(max(0, idx - 3), idx):
            context_lines.append(lines[i].strip())

        line = lines[idx]
        text = line.replace(self._get_tag("best_practice"), "").strip()
        text = re.sub(r"^[-*\d.]+\s*", "", text)

        if not text:
            return None

        return {
            "title": text[:80],
            "context": " ".join(context_lines)[:200] or "Tagged best practice",
            "practice": text,
            "benefit": "To be documented",
            "extracted_from": idx + 1,
            "status": "pending_validation",
            "auto_detected": False,
            "timestamp": datetime.now().isoformat(),
        }

    def _parse_solution_section(
        self, lines: List[str], start_idx: int
    ) -> Optional[Dict]:
        """
        Parse a solution section for best practices.

        Args:
            lines: List of lines from the file.
            start_idx: Index of the section header.

        Returns:
            Practice dictionary or None.
        """
        solution_lines = []
        for i in range(start_idx + 1, min(len(lines), start_idx + 15)):
            if lines[i].startswith("## "):
                break
            solution_lines.append(lines[i])

        text = " ".join(line.strip() for line in solution_lines if line.strip())
        text = re.sub(r"\s+", " ", text)

        if len(text) < 20:
            return None

        return {
            "title": text[:80],
            "context": "Auto-detected from Solucion section",
            "practice": text,
            "benefit": "Resolved an issue during session",
            "extracted_from": start_idx + 1,
            "status": "pending_validation",
            "auto_detected": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _parse_code_solution(self, lines: List[str], idx: int) -> Optional[Dict]:
        """
        Parse a code solution that worked.

        Args:
            lines: List of lines from the file.
            idx: Index of the success indicator line.

        Returns:
            Practice dictionary or None.
        """
        code_start = None
        code_content = []

        for i in range(idx - 1, max(0, idx - 20), -1):
            if "```" in lines[i]:
                code_start = i
                break

        if code_start is None:
            return None

        for i in range(code_start + 1, idx):
            if "```" in lines[i]:
                break
            code_content.append(lines[i])

        code_text = "\n".join(code_content).strip()
        if not code_text:
            return None

        return {
            "title": f"Code solution ({len(code_content)} lines)",
            "context": lines[idx].strip(),
            "practice": code_text,
            "benefit": "Successfully resolved an issue",
            "extracted_from": code_start + 1,
            "status": "validated",
            "auto_detected": True,
            "timestamp": datetime.now().isoformat(),
        }

    def update_discoveries_file(self, discoveries: List[Dict]) -> bool:
        """
        Append discoveries to discoveries.md with pending_validation status.

        Args:
            discoveries: List of discovery dictionaries.

        Returns:
            True if successful, False otherwise.
        """
        if not discoveries:
            return True

        try:
            for discovery in discoveries:
                date_str = datetime.now().strftime("%Y-%m-%d")
                detection = (
                    "automatica"
                    if discovery.get("auto_detected")
                    else f"tag {self._get_tag('discovery')}"
                )

                entry = f"""### {date_str}: [PENDIENTE VALIDACION] {discovery.get("title", "Untitled")}

> **Estado**: pendiente_validacion
> **Extraido de**: sessions/{discovery.get("session_file", "unknown")}#L{discovery.get("extracted_from", 0)}
> **Deteccion**: {detection}

**Contexto**: {discovery.get("context", "N/A")}

**Descubrimiento**: {discovery.get("discovery", "N/A")}

**Impacto**: {discovery.get("impact", "N/A")}

---

"""
                self._append_to_md(self.discoveries_file, entry)

            return True
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to update discoveries: {e}", Colors.RED))
            return False

    def update_prompts_registry(self, prompts: List[Dict]) -> bool:
        """
        Update prompts/registry.json with new prompts.

        Args:
            prompts: List of prompt dictionaries.

        Returns:
            True if successful, False otherwise.
        """
        if not prompts:
            return True

        try:
            registry = self._read_json(self.prompts_file)
            if not registry:
                registry = {"prompts": [], "last_updated": None}

            existing_ids = {p.get("id") for p in registry.get("prompts", [])}

            for prompt in prompts:
                if prompt.get("id") not in existing_ids:
                    registry["prompts"].append(prompt)

            registry["last_updated"] = datetime.now().isoformat()
            self._write_json(self.prompts_file, registry)

            return True
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to update prompts registry: {e}", Colors.RED))
            return False

    def update_ideas_file(self, ideas: List[Dict]) -> bool:
        """
        Append ideas to ideas.md.

        Args:
            ideas: List of idea dictionaries.

        Returns:
            True if successful, False otherwise.
        """
        if not ideas:
            return True

        try:
            for idea in ideas:
                date_str = datetime.now().strftime("%Y-%m-%d")
                status = idea.get("status", "pending")
                status_text = "VALIDADA" if status == "validated" else "PENDIENTE"

                entry = f"""### {date_str}: [{status_text}] {idea.get("title", "Untitled")}

> **Estado**: {status}
> **Prioridad**: {idea.get("priority", "medium")}
> **Extraido de**: session#L{idea.get("extracted_from", 0)}
> **Deteccion**: {"automatica" if idea.get("auto_detected") else f"tag {self._get_tag('idea')}"}

**Descripcion**: {idea.get("description", "N/A")}

---

"""
                self._append_to_md(self.ideas_file, entry)

            return True
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to update ideas: {e}", Colors.RED))
            return False

    def update_best_practices_file(self, practices: List[Dict]) -> bool:
        """
        Append best practices to best-practices.md.

        Args:
            practices: List of practice dictionaries.

        Returns:
            True if successful, False otherwise.
        """
        if not practices:
            return True

        try:
            for practice in practices:
                date_str = datetime.now().strftime("%Y-%m-%d")
                status = practice.get("status", "pending_validation")
                status_text = (
                    "VALIDADA" if status == "validated" else "PENDIENTE VALIDACION"
                )
                detection = (
                    "automatica"
                    if practice.get("auto_detected")
                    else f"tag {self._get_tag('best_practice')}"
                )

                entry = f"""### {date_str}: [{status_text}] {practice.get("title", "Untitled")}

> **Estado**: {status}
> **Extraido de**: session#L{practice.get("extracted_from", 0)}
> **Deteccion**: {detection}

**Contexto**: {practice.get("context", "N/A")}

**Practica**: {practice.get("practice", "N/A")[:500]}

**Beneficio**: {practice.get("benefit", "N/A")}

---

"""
                self._append_to_md(self.best_practices_file, entry)

            return True
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to update best practices: {e}", Colors.RED))
            return False

    def update_knowledge_index(self, stats: Dict) -> bool:
        """
        Update knowledge-index.json with counts and stats.

        Args:
            stats: Dictionary with extraction statistics.

        Returns:
            True if successful, False otherwise.
        """
        try:
            index = self._read_json(self.index_file)
            if not index:
                index = {}

            if "discoveries" not in index:
                index["discoveries"] = 0
            if "prompts" not in index:
                index["prompts"] = 0
            if "ideas" not in index:
                index["ideas"] = 0
            if "best_practices" not in index:
                index["best_practices"] = 0
            if "last_extraction" not in index:
                index["last_extraction"] = None
            if "history" not in index:
                index["history"] = []

            index["discoveries"] += stats.get("discoveries", 0)
            index["prompts"] += stats.get("prompts", 0)
            index["ideas"] += stats.get("ideas", 0)
            index["best_practices"] += stats.get("best_practices", 0)
            index["last_extraction"] = datetime.now().isoformat()

            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "session": stats.get("session_file", "unknown"),
                "discoveries": stats.get("discoveries", 0),
                "prompts": stats.get("prompts", 0),
                "ideas": stats.get("ideas", 0),
                "best_practices": stats.get("best_practices", 0),
            }
            index["history"].append(history_entry)

            if len(index["history"]) > 100:
                index["history"] = index["history"][-100:]

            self._write_json(self.index_file, index)

            return True
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to update index: {e}", Colors.RED))
            return False

    def extract_all_knowledge(self, session_file: Path) -> Dict:
        """
        Main function - extract all knowledge types.

        Args:
            session_file: Path to the session markdown file.

        Returns:
            Dict with counts of each type extracted:
            - discoveries: count
            - prompts: count
            - ideas: count
            - best_practices: count
            - success: bool
            - session_file: str
        """
        if not self.config.get("enabled", True):
            return {
                "discoveries": 0,
                "prompts": 0,
                "ideas": 0,
                "best_practices": 0,
                "success": False,
                "session_file": str(session_file),
                "message": "Knowledge extraction disabled",
            }

        discoveries = self.extract_session_discoveries(session_file)
        prompts = self.extract_successful_prompts(session_file)
        ideas = self.extract_validated_ideas(session_file)
        practices = self.extract_best_practices(session_file)

        for d in discoveries:
            d["session_file"] = session_file.name
        for p in prompts:
            p["session_file"] = session_file.name
        for i in ideas:
            i["session_file"] = session_file.name
        for p in practices:
            p["session_file"] = session_file.name

        stats = {
            "discoveries": len(discoveries),
            "prompts": len(prompts),
            "ideas": len(ideas),
            "best_practices": len(practices),
            "session_file": session_file.name,
        }

        success = True
        success &= self.update_discoveries_file(discoveries)
        success &= self.update_prompts_registry(prompts)
        success &= self.update_ideas_file(ideas)
        success &= self.update_best_practices_file(practices)
        success &= self.update_knowledge_index(stats)

        return {
            **stats,
            "success": success,
        }


def extract_session_discoveries(session_file: Path) -> List[Dict]:
    """Convenience function to extract discoveries."""
    extractor = KnowledgeExtractor()
    return extractor.extract_session_discoveries(session_file)


def extract_successful_prompts(session_file: Path) -> List[Dict]:
    """Convenience function to extract prompts."""
    extractor = KnowledgeExtractor()
    return extractor.extract_successful_prompts(session_file)


def extract_validated_ideas(session_file: Path) -> List[Dict]:
    """Convenience function to extract ideas."""
    extractor = KnowledgeExtractor()
    return extractor.extract_validated_ideas(session_file)


def extract_best_practices(session_file: Path) -> List[Dict]:
    """Convenience function to extract best practices."""
    extractor = KnowledgeExtractor()
    return extractor.extract_best_practices(session_file)


def update_discoveries_file(discoveries: List[Dict]) -> bool:
    """Convenience function to update discoveries file."""
    extractor = KnowledgeExtractor()
    return extractor.update_discoveries_file(discoveries)


def update_prompts_registry(prompts: List[Dict]) -> bool:
    """Convenience function to update prompts registry."""
    extractor = KnowledgeExtractor()
    return extractor.update_prompts_registry(prompts)


def update_ideas_file(ideas: List[Dict]) -> bool:
    """Convenience function to update ideas file."""
    extractor = KnowledgeExtractor()
    return extractor.update_ideas_file(ideas)


def update_best_practices_file(practices: List[Dict]) -> bool:
    """Convenience function to update best practices file."""
    extractor = KnowledgeExtractor()
    return extractor.update_best_practices_file(practices)


def update_knowledge_index(stats: Dict) -> bool:
    """Convenience function to update knowledge index."""
    extractor = KnowledgeExtractor()
    return extractor.update_knowledge_index(stats)


def extract_all_knowledge(session_file: Path) -> Dict:
    """Convenience function to extract all knowledge."""
    extractor = KnowledgeExtractor()
    return extractor.extract_all_knowledge(session_file)


def _create_test_session_file() -> Path:
    """Create a test session file for self-test."""
    test_content = """# Session 2026-03-11

## Inicio

**Hora**: 10:00

## Hallazgos

- Descubrimiento: El nuevo patron de error handling funciona mejor
- El modulo de extraction puede ser reutilizado #discovery

## Solucion

Se resolvio el problema de encoding usando:

```python
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

Esto funciono correctamente. [OK]

## Ideas

- [x] Implementar nuevo modulo de extraction
- [ ] Agregar soporte para YAML

## Prompt Exitoso

#prompt-success

```python
def extract_patterns(text):
    return re.findall(r'pattern', text)
```

Exitoso - funciono perfectamente.

---

## Best Practice

Usar siempre `encoding='utf-8'` al leer archivos en Windows #best-practice
"""
    test_file = Path(__file__).parent / "test_session.md"
    test_file.write_text(test_content, encoding="utf-8")
    return test_file


if __name__ == "__main__":
    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("Knowledge Extractor Module Test", Colors.BOLD + Colors.CYAN))
    print(c("=" * 50, Colors.HEADER))

    extractor = KnowledgeExtractor()

    test_file = _create_test_session_file()
    print(c(f"\n[SETUP] Created test session file: {test_file}", Colors.DIM))

    print(c("\n[TEST 1] Extracting discoveries...", Colors.CYAN))
    discoveries = extractor.extract_session_discoveries(test_file)
    print(f"  Found: {len(discoveries)} discoveries")
    for d in discoveries[:2]:
        print(f"    - {d['title'][:50]}...")
        print(f"      Auto-detected: {d['auto_detected']}")

    print(c("\n[TEST 2] Extracting successful prompts...", Colors.CYAN))
    prompts = extractor.extract_successful_prompts(test_file)
    print(f"  Found: {len(prompts)} prompts")
    for p in prompts[:2]:
        print(f"    - {p['id']} ({p['category']})")

    print(c("\n[TEST 3] Extracting validated ideas...", Colors.CYAN))
    ideas = extractor.extract_validated_ideas(test_file)
    print(f"  Found: {len(ideas)} ideas")
    for i in ideas[:2]:
        print(f"    - {i['title'][:50]}... (status: {i['status']})")

    print(c("\n[TEST 4] Extracting best practices...", Colors.CYAN))
    practices = extractor.extract_best_practices(test_file)
    print(f"  Found: {len(practices)} practices")
    for p in practices[:2]:
        print(f"    - {p['title'][:50]}...")

    print(c("\n[TEST 5] Running full extraction...", Colors.CYAN))
    results = extractor.extract_all_knowledge(test_file)
    print(f"  Discoveries: {results['discoveries']}")
    print(f"  Prompts: {results['prompts']}")
    print(f"  Ideas: {results['ideas']}")
    print(f"  Best practices: {results['best_practices']}")
    print(f"  Success: {results['success']}")

    print(c("\n[TEST 6] Verifying output files...", Colors.CYAN))
    files_to_check = [
        ("Discoveries", extractor.discoveries_file),
        ("Prompts", extractor.prompts_file),
        ("Ideas", extractor.ideas_file),
        ("Best practices", extractor.best_practices_file),
        ("Index", extractor.index_file),
    ]
    for name, path in files_to_check:
        exists = path.exists()
        status = c("[OK]", Colors.GREEN) if exists else c("[MISSING]", Colors.RED)
        print(f"  {name}: {status}")

    print(c("\n[TEST 7] Reading knowledge index...", Colors.CYAN))
    index = extractor._read_json(extractor.index_file)
    print(f"  Total discoveries: {index.get('discoveries', 0)}")
    print(f"  Total prompts: {index.get('prompts', 0)}")
    print(f"  Total ideas: {index.get('ideas', 0)}")
    print(f"  Total best practices: {index.get('best_practices', 0)}")
    print(f"  History entries: {len(index.get('history', []))}")

    test_file.unlink()
    print(c(f"\n[CLEANUP] Removed test file", Colors.DIM))

    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("Tests completed successfully!", Colors.GREEN))
    print(c("=" * 50, Colors.HEADER))

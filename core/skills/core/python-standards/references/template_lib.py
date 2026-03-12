#!/usr/bin/env python3
"""
Library Module Template

A production-ready template for Python library modules.
Designed for import and reuse without console output.

This module provides [brief description of functionality].

Example Usage:
    >>> from template_lib import process_items, validate_config
    >>> config = validate_config({"key": "value"})
    >>> result = process_items(["item1", "item2"])

Attributes:
    __version__: Module version string.
    DEFAULT_TIMEOUT: Default timeout in seconds for operations.

Exceptions:
    LibraryError: Base exception for all library errors.
    ValidationError: Raised when configuration validation fails.
    ProcessingError: Raised when data processing fails.
"""

from typing import Any, Dict, List, Optional, Union

__version__ = "1.0.0"
DEFAULT_TIMEOUT = 30


class LibraryError(Exception):
    """Base exception for all library errors.

    All custom exceptions in this module inherit from this class.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize the exception.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional error context.
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(LibraryError):
    """Exception raised when configuration or data validation fails."""

    pass


class ProcessingError(LibraryError):
    """Exception raised when data processing operations fail."""

    pass


class ConfigItem:
    """Represents a configuration item with validation.

    Attributes:
        name: Configuration item name.
        value: Configuration item value.
        required: Whether this item is required.
    """

    def __init__(self, name: str, value: Any, required: bool = True):
        """Initialize configuration item.

        Args:
            name: Configuration item identifier.
            value: Configuration item value.
            required: Whether this item must have a value.
        """
        self.name = name
        self.value = value
        self.required = required

    def is_valid(self) -> bool:
        """Check if the configuration item is valid.

        Returns:
            True if valid (has value or is not required), False otherwise.
        """
        if self.required and self.value is None:
            return False
        return True


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a configuration dictionary.

    Args:
        config: Dictionary containing configuration options.

    Returns:
        Validated configuration dictionary.

    Raises:
        ValidationError: If configuration is invalid or missing required fields.

    Example:
        >>> config = validate_config({"timeout": 60, "retries": 3})
        >>> print(config["timeout"])
        60
    """
    if not isinstance(config, dict):
        raise ValidationError(
            "Configuration must be a dictionary",
            details={"type_received": type(config).__name__},
        )

    required_keys = ["timeout", "retries"]
    missing_keys = [key for key in required_keys if key not in config]

    if missing_keys:
        raise ValidationError(
            f"Missing required configuration keys: {missing_keys}",
            details={
                "missing_keys": missing_keys,
                "provided_keys": list(config.keys()),
            },
        )

    # Validate timeout is a positive integer
    timeout = config.get("timeout")
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValidationError(
            "Timeout must be a positive integer",
            details={"timeout_value": timeout, "timeout_type": type(timeout).__name__},
        )

    return config


def process_items(
    items: List[str], options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process a list of items with optional configuration.

    Args:
        items: List of string items to process.
        options: Optional processing options dictionary.

    Returns:
        Dictionary containing processing results with keys:
            - success: Boolean indicating if processing succeeded
            - processed_count: Number of items processed
            - results: List of processed item results
            - errors: List of any errors encountered

    Raises:
        ProcessingError: If processing fails catastrophically.
        ValidationError: If input validation fails.

    Example:
        >>> items = ["item1", "item2", "item3"]
        >>> result = process_items(items, {"timeout": 60})
        >>> print(result["processed_count"])
        3
    """
    if items is None:
        raise ValidationError(
            "Items list cannot be None", details={"parameter": "items"}
        )

    if not isinstance(items, list):
        raise ValidationError(
            "Items must be a list", details={"type_received": type(items).__name__}
        )

    options = options or {}

    results = {
        "success": True,
        "processed_count": 0,
        "results": [],
        "errors": [],
    }

    for index, item in enumerate(items):
        try:
            if not isinstance(item, str):
                raise ValidationError(
                    f"Item at index {index} must be a string",
                    details={"index": index, "type": type(item).__name__},
                )

            # TODO: Add actual processing logic here
            processed = f"processed_{item}"
            results["results"].append(processed)
            results["processed_count"] += 1

        except ValidationError as e:
            results["errors"].append(
                {
                    "index": index,
                    "item": item,
                    "error": e.message,
                }
            )
            results["success"] = False

        except Exception as e:
            raise ProcessingError(
                f"Unexpected error processing item at index {index}: {e}",
                details={"index": index, "item": item, "error_type": type(e).__name__},
            )

    return results


def transform_data(
    data: Union[str, List[str]], transformation: str = "upper"
) -> Union[str, List[str]]:
    """Transform data according to specified transformation.

    Args:
        data: Input data as string or list of strings.
        transformation: Type of transformation to apply.
            Options: "upper", "lower", "reverse", "none"

    Returns:
        Transformed data in the same type as input.

    Raises:
        ValidationError: If transformation type is invalid.

    Example:
        >>> transform_data("hello", "upper")
        'HELLO'
        >>> transform_data(["a", "b"], "reverse")
        ['b', 'a']
    """
    valid_transformations = ["upper", "lower", "reverse", "none"]

    if transformation not in valid_transformations:
        raise ValidationError(
            f"Invalid transformation: {transformation}",
            details={
                "valid_options": valid_transformations,
                "received": transformation,
            },
        )

    def _transform_single(item: str) -> str:
        if transformation == "upper":
            return item.upper()
        elif transformation == "lower":
            return item.lower()
        elif transformation == "reverse":
            return item[::-1]
        else:  # "none"
            return item

    if isinstance(data, str):
        return _transform_single(data)
    elif isinstance(data, list):
        return [_transform_single(item) for item in data]
    else:
        raise ValidationError(
            "Data must be a string or list of strings",
            details={"type_received": type(data).__name__},
        )


def get_module_info() -> Dict[str, str]:
    """Return information about this module.

    Returns:
        Dictionary containing module metadata.
    """
    return {
        "name": "template_lib",
        "version": __version__,
        "description": "Library module template",
        "default_timeout": str(DEFAULT_TIMEOUT),
    }

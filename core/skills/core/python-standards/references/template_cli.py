#!/usr/bin/env python3
"""
CLI Script Template

A production-ready template for command-line interface scripts.
Features automatic environment detection, safe emoji output, and
cross-platform compatibility.

Usage:
    python template_cli.py [options]
    ./template_cli.py --help

Examples:
    python template_cli.py --input data.txt
    python template_cli.py --verbose --output result.json
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Import framework utilities
try:
    from detect_env import SafePrinter, configure_stdout, should_use_emojis
except ImportError:
    # Fallback if detect_env is not available
    class SafePrinter:
        """Fallback SafePrinter when detect_env is not available."""

        def success(self, msg: str) -> None:
            print(f"[OK] {msg}")

        def error(self, msg: str) -> None:
            print(f"[ERROR] {msg}", file=sys.stderr)

        def warning(self, msg: str) -> None:
            print(f"[WARN] {msg}")

        def info(self, msg: str) -> None:
            print(f"[INFO] {msg}")

    def configure_stdout() -> None:
        """Fallback configure_stdout."""
        pass

    def should_use_emojis() -> bool:
        """Fallback should_use_emojis."""
        return False


class CLIError(Exception):
    """Exception for CLI-related errors."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(self.message)


def parse_arguments() -> argparse.Namespace:
    """
    Parse and return command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="CLI Script Template - Description of what this script does.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --input file.txt
    %(prog)s --verbose --output result.json
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Path to input file",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Path to output file (default: stdout)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    return parser.parse_args()


def validate_input_file(file_path: str) -> Path:
    """
    Validate that the input file exists and is readable.

    Args:
        file_path: Path to the input file.

    Returns:
        Validated Path object.

    Raises:
        CLIError: If file does not exist or is not readable.
    """
    path = Path(file_path)

    if not path.exists():
        raise CLIError(f"Input file not found: {file_path}", exit_code=2)

    if not path.is_file():
        raise CLIError(f"Input path is not a file: {file_path}", exit_code=2)

    if not path.is_file():
        raise CLIError(f"Input path is not a file: {file_path}", exit_code=2)

    return path


def process_data(input_path: Optional[Path], verbose: bool = False) -> str:
    """
    Process data from input and return result.

    Args:
        input_path: Path to input file (None for stdin).
        verbose: Whether to print verbose messages.

    Returns:
        Processed data as string.

    Raises:
        CLIError: If processing fails.
    """
    try:
        if input_path:
            if verbose:
                print(f"Reading from: {input_path}")
            content = input_path.read_text(encoding="utf-8")
        else:
            if verbose:
                print("Reading from stdin")
            content = sys.stdin.read()

        # TODO: Add your processing logic here
        result = f"Processed: {len(content)} characters"

        return result

    except UnicodeDecodeError as e:
        raise CLIError(f"Failed to decode input file: {e}", exit_code=3)
    except IOError as e:
        raise CLIError(f"I/O error while processing: {e}", exit_code=3)


def write_output(result: str, output_path: Optional[str]) -> None:
    """
    Write result to output file or stdout.

    Args:
        result: Content to write.
        output_path: Path to output file (None for stdout).

    Raises:
        CLIError: If writing fails.
    """
    try:
        if output_path:
            path = Path(output_path)
            path.write_text(result, encoding="utf-8")
        else:
            print(result)
    except IOError as e:
        raise CLIError(f"Failed to write output: {e}", exit_code=4)


def main() -> int:
    """
    Main entry point for the CLI script.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    # Configure stdout for cross-platform compatibility
    configure_stdout()

    # Initialize safe printer
    printer = SafePrinter()

    try:
        # Parse arguments
        args = parse_arguments()

        if args.verbose:
            printer.info("Starting processing...")
            printer.info(f"Arguments: {args}")

        # Validate input
        input_path = None
        if args.input:
            input_path = validate_input_file(args.input)

        # Dry run check
        if args.dry_run:
            printer.warning("DRY RUN MODE - No changes will be made")
            if input_path:
                printer.info(f"Would process: {input_path}")
            if args.output:
                printer.info(f"Would write to: {args.output}")
            return 0

        # Process data
        result = process_data(input_path, verbose=args.verbose)

        # Write output
        write_output(result, args.output)

        printer.success("Operation completed successfully")
        return 0

    except CLIError as e:
        printer.error(e.message)
        return e.exit_code
    except KeyboardInterrupt:
        printer.warning("Operation cancelled by user")
        return 130
    except Exception as e:
        printer.error(f"Unexpected error: {e}")
        if args.verbose:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())

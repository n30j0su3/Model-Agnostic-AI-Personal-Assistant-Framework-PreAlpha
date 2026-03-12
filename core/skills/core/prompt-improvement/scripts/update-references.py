#!/usr/bin/env python3
import argparse
import datetime
import json
from pathlib import Path


def load_lines(path):
    return path.read_text(encoding="utf-8").splitlines()


def save_lines(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_revision(lines, date_str):
    for idx, line in enumerate(lines):
        if line.startswith("Ultima revision:"):
            lines[idx] = f"Ultima revision: {date_str}"
            return True
    return False


def extract_references(lines):
    refs = []
    for line in lines:
        if line.startswith("- "):
            refs.append(line[2:].strip())
    return refs


def output(data, as_json):
    if as_json:
        print(json.dumps(data, ensure_ascii=True, indent=2))
        return
    if isinstance(data, list):
        for item in data:
            print(item)
        return
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{key}: {value}")
        return
    print(data)


def main():
    parser = argparse.ArgumentParser(description="Update prompt-improvement references")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--print", action="store_true", help="Print references list")
    parser.add_argument("--date", help="Override date (YYYY-MM-DD)")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    skill_root = script_path.parents[1]
    references_path = skill_root / "references.md"
    if not references_path.exists():
        output({"ok": False, "error": "references.md not found"}, args.json)
        raise SystemExit(1)

    lines = load_lines(references_path)
    date_str = args.date or datetime.date.today().isoformat()
    updated = update_revision(lines, date_str)
    if updated:
        save_lines(references_path, lines)

    refs = extract_references(lines)
    if args.print:
        output(refs, False)
        return

    output({"ok": updated, "date": date_str, "references": refs}, args.json)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
RUBRICS_DIR = SKILL_ROOT / "rubrics"


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[ERROR] No se pudo leer {path}: {exc}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Context Evaluator CLI (LLM-as-a-Judge)"
    )
    parser.add_argument("--prompt", help="El prompt original enviado al agente")
    parser.add_argument("--response", help="La respuesta generada por el agente")
    parser.add_argument(
        "--rubric",
        default="general",
        help="Nombre de la rubrica a usar (ej: general, technical)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Salida en formato JSON puro"
    )
    args = parser.parse_args()

    rubric_path = RUBRICS_DIR / f"{args.rubric}.json"
    if not rubric_path.exists():
        print(f"[ERROR] No se encontro la rubrica: {args.rubric}", file=sys.stderr)
        return 1

    rubric = load_json(rubric_path)
    if not rubric:
        return 1

    if not args.prompt or not args.response:
        # Si no hay entrada, generamos un template para el LLM
        output = {
            "status": "template_mode",
            "message": "Generando plantilla de evaluacion para el LLM",
            "rubric": rubric,
            "instruction": "Evalua la respuesta del agente basandote en los criterios de la rubrica proporcionada.",
        }
    else:
        # Generamos la estructura de evaluacion
        output = {
            "status": "evaluation_ready",
            "rubric_name": rubric.get("name"),
            "input": {"prompt": args.prompt, "response": args.response},
            "evaluation_criteria": rubric.get("criteria", []),
            "template": {
                "scores": {c["id"]: 0 for c in rubric.get("criteria", [])},
                "justifications": {c["id"]: "" for c in rubric.get("criteria", [])},
                "overall_summary": "",
                "improvement_suggestions": [],
            },
        }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = SKILL_ROOT / "local-rules.json"
AGENTS_PATH = SKILL_ROOT / "agent-routing.json"


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"No se pudo leer {path}: {exc}")


def normalize(text):
    return " ".join(text.strip().lower().split())


def match_local_rules(text, rules):
    for rule in rules:
        pattern = rule.get("pattern")
        if not pattern:
            continue
        if re.match(pattern, text, flags=re.IGNORECASE):
            return rule
    return None


def extract_agent_mentions(text, agents):
    mentions = re.findall(r"@([a-zA-Z0-9\-]+)", text)
    if not mentions:
        return None
    normalized = {f"@{m.lower()}" for m in mentions}
    for agent in agents:
        if agent.lower() in normalized:
            return agent
    return None


def score_agents(text, agent_map):
    scores = {}
    for agent, keywords in agent_map.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text:
                score += 1
        if score:
            scores[agent] = score
    if not scores:
        return None, 0
    best_agent = max(scores, key=scores.get)
    return best_agent, scores[best_agent]


def route_instruction(text, rules, agent_map, threshold):
    normalized = normalize(text)

    local_rule = match_local_rules(normalized, rules)
    if local_rule:
        return {
            "type": "LOCAL_EXECUTION",
            "action": local_rule.get("action"),
            "rule": local_rule.get("id"),
            "reason": local_rule.get("description", "match de regla local"),
        }

    explicit_agent = extract_agent_mentions(normalized, agent_map.keys())
    if explicit_agent:
        return {
            "type": "DELEGATE",
            "agent": explicit_agent,
            "reason": "mencion explicita de agente",
        }

    best_agent, score = score_agents(normalized, agent_map)
    if best_agent and score >= threshold:
        return {
            "type": "DELEGATE",
            "agent": best_agent,
            "reason": f"intencion detectada (score={score})",
        }

    return {
        "type": "REMOTE_LLM",
        "reason": "sin match local ni delegacion",
    }


def list_rules(rules):
    for rule in rules:
        print(f"- {rule.get('id')}: {rule.get('description')}")


def list_agents(agent_map):
    for agent, keywords in agent_map.items():
        keywords_text = ", ".join(keywords)
        print(f"- {agent}: {keywords_text}")


def main():
    parser = argparse.ArgumentParser(description="Decision Engine Router")
    parser.add_argument("input", nargs="?", help="Texto de entrada")
    parser.add_argument(
        "--threshold", type=int, default=2, help="Umbral para delegacion implicita"
    )
    parser.add_argument("--explain", action="store_true", help="Incluir explicacion")
    parser.add_argument(
        "--list-rules", action="store_true", help="Listar reglas locales"
    )
    parser.add_argument(
        "--list-agents", action="store_true", help="Listar agentes y keywords"
    )
    args = parser.parse_args()

    rules = load_json(RULES_PATH)
    agents = load_json(AGENTS_PATH)

    if args.list_rules:
        list_rules(rules)
        return 0
    if args.list_agents:
        list_agents(agents)
        return 0

    text = args.input
    if not text:
        if sys.stdin.isatty():
            print("[ERROR] Debes proporcionar un texto de entrada.")
            return 1
        text = sys.stdin.read()

    decision = route_instruction(text, rules, agents, args.threshold)
    if not args.explain:
        decision.pop("reason", None)

    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Research Tool - BL-104: Research & Improvement Capability
Analiza gaps entre Knowledge Base y skills locales del framework

Uso:
    python core/scripts/research-tool.py
    python core/scripts/research-tool.py --topic "Productivity"
    python core/scripts/research-tool.py --json
"""

import argparse
import json
import sys
from pathlib import Path


def find_repo_root():
    """Encuentra la raíz del repo buscando la estructura core/."""
    script_path = Path(__file__).resolve()
    for candidate in [script_path.parent] + list(script_path.parents):
        if (candidate / "core" / ".context").exists():
            return candidate
    return None


def load_json(path):
    """Carga un archivo JSON de manera segura."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Fallo al cargar {path.name}: {e}", file=sys.stderr)
        return {}


def get_skills_from_catalog(catalog_path):
    """Extrae skills del catalog.json."""
    catalog = load_json(catalog_path)
    skills = catalog.get("skills", {})

    skill_categories = {}
    for skill_id, skill_info in skills.items():
        cat = skill_info.get("category", "Uncategorized")
        if cat not in skill_categories:
            skill_categories[cat] = []
        skill_categories[cat].append(
            {
                "id": skill_id,
                "name": skill_info.get("name", skill_id),
                "description": skill_info.get("description", ""),
            }
        )

    return skill_categories


def get_research_recommendations(kb_path, catalog_path, topic=None, output_json=False):
    """
    Analiza la knowledge base y compara con skills existentes.
    Retorna recomendaciones de research.
    """
    kb = load_json(kb_path)
    skill_categories = get_skills_from_catalog(catalog_path)

    output = []
    output.append("# 🔬 Research & Improvement Analysis\n")

    # 1. Información general
    kb_categories = kb.get("categories", {})
    output.append(f"**Knowledge Base Categories:** {len(kb_categories)}")
    output.append(f"**Local Skill Categories:** {len(skill_categories)}\n")

    # 2. Comparar categorías - Gaps
    output.append("## Gaps vs Knowledge Base\n")
    gaps_found = False

    for cat_name, items in kb_categories.items():
        # Si hay filtro por topic, aplicarlo
        if topic and topic.lower() not in cat_name.lower():
            continue

        cat_key = cat_name.lower()
        if cat_key not in [k.lower() for k in skill_categories.keys()]:
            output.append(f"### ❌ {cat_name}")
            output.append("Categoría encontrada en KB pero no en skills locales.")
            if items:
                output.append("**Sugerencias:**")
                for item in items:
                    if isinstance(item, dict):
                        name = item.get("name", "Unknown")
                        desc = item.get("description", "")
                        url = item.get("url", "")
                        output.append(f"  - {name}: {desc}")
                        if url:
                            output.append(f"    URL: {url}")
                    else:
                        output.append(f"  - {item}")
            output.append("")
            gaps_found = True

    if not gaps_found:
        output.append("✅ No se encontraron gaps de categorías inmediatos.\n")

    # 3. Categorías existentes - Oportunidades de mejora
    output.append("## Oportunidades de Optimización\n")

    for cat_name in skill_categories.keys():
        cat_key = cat_name.lower()
        kb_match = None
        for kb_cat, kb_items in kb_categories.items():
            if kb_cat.lower() == cat_key:
                kb_match = (kb_cat, kb_items)
                break

        if kb_match:
            kb_cat_name, kb_items = kb_match
            output.append(f"### 📊 {cat_name} (Local existe)")
            output.append(f"Skills locales: {len(skill_categories[cat_name])}")
            if kb_items:
                output.append("**Referencias de KB para mejoras:**")
                for item in kb_items[:3]:  # Limitar a 3 para no saturar
                    if isinstance(item, dict):
                        name = item.get("name", "Unknown")
                        desc = item.get("description", "")[:60]  # Truncar
                        output.append(f"  - {name}: {desc}...")
                    else:
                        output.append(f"  - {item}")
            output.append("")
        else:
            output.append(f"### ✅ {cat_name} (Local only)")
            output.append("Categoría solo existe localmente.\n")

    # 4. Resumen ejecutivo
    output.append("---\n")
    output.append("## Resumen Ejecutivo\n")
    total_kb = len(kb_categories)
    total_local = len(skill_categories)
    matched = sum(
        1
        for cat in skill_categories.keys()
        if cat.lower() in [k.lower() for k in kb_categories.keys()]
    )

    output.append(f"- **Categorías en KB:** {total_kb}")
    output.append(f"- **Categorías locales:** {total_local}")
    output.append(f"- **Categorías coincidentes:** {matched}")
    output.append(f"- **Gaps identificados:** {total_kb - matched}")

    if topic:
        output.append(f"\n*Filtrado por tema: '{topic}'*")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Research Tool - Analiza gaps entre KB y skills locales"
    )
    parser.add_argument("--topic", help="Filtrar research por tema específico")
    parser.add_argument("--json", action="store_true", help="Output en formato JSON")
    args = parser.parse_args()

    # Encontrar rutas
    repo_root = find_repo_root()
    if not repo_root:
        print("[ERROR] No se encontró la raíz del repositorio", file=sys.stderr)
        sys.exit(1)

    kb_path = repo_root / "core" / ".context" / "knowledge_base.json"
    catalog_path = repo_root / "core" / "skills" / "catalog.json"

    # Verificar que existan
    if not kb_path.exists():
        print(f"[WARNING] Knowledge base no encontrada: {kb_path}", file=sys.stderr)
        print("Creando KB vacía...", file=sys.stderr)
        # Crear KB mínima
        kb_path.parent.mkdir(parents=True, exist_ok=True)
        kb_path.write_text(
            json.dumps(
                {"categories": {}, "version": "1.0", "last_updated": "2026-02-11"},
                indent=2,
            ),
            encoding="utf-8",
        )

    if not catalog_path.exists():
        print(
            f"[ERROR] Catalog de skills no encontrado: {catalog_path}", file=sys.stderr
        )
        sys.exit(1)

    # Generar reporte
    report = get_research_recommendations(kb_path, catalog_path, args.topic, args.json)
    print(report)


if __name__ == "__main__":
    main()

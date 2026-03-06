#!/usr/bin/env python3
"""
Knowledge Indexer - PA Framework
================================

Genera insights automáticos a partir de logs de interacciones.

Uso:
    python core/scripts/knowledge-indexer.py           # Generar insights del día
    python core/scripts/knowledge-indexer.py --date=YYYY-MM-DD  # Fecha específica

Autor: FreakingJSON-PA Framework
Versión: 1.0.0 (BL-100)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONTEXT_DIR = REPO_ROOT / "core" / ".context"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
INTERACTIONS_DIR = KNOWLEDGE_DIR / "interactions"
INSIGHTS_DIR = KNOWLEDGE_DIR / "insights"

# Ensure directories exist
INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)


def read_interactions(date: str) -> List[Dict]:
    """Leer interacciones del día especificado."""
    log_file = INTERACTIONS_DIR / f"interactions-{date}.log"
    if not log_file.exists():
        return []
    
    interactions = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                interactions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return interactions


def extract_top_phrases(interactions: List[Dict], n: int = 10) -> List[Tuple[str, int]]:
    """Extraer frases/patrones más empleados."""
    # Simplificado: contar agentes y modelos más usados
    agents = [i.get('agent', 'unknown') for i in interactions if 'agent' in i]
    models = [i.get('model', 'unknown') for i in interactions if 'model' in i]
    event_types = [i.get('event', 'unknown') for i in interactions]
    
    counter = Counter(agents + models + event_types)
    return counter.most_common(n)


def classify_by_category(interactions: List[Dict]) -> Dict[str, int]:
    """Clasificar interacciones por categoría/workspace."""
    categories = {
        'development': 0,
        'documentation': 0,
        'research': 0,
        'personal': 0,
        'other': 0
    }
    
    for interaction in interactions:
        event = interaction.get('event', '')
        agent = interaction.get('agent', '')
        
        if event == 'file_write' and 'docs/' in interaction.get('file', ''):
            categories['documentation'] += 1
        elif event == 'file_write' and 'core/' in interaction.get('file', ''):
            categories['development'] += 1
        elif 'research' in agent.lower() or 'scout' in agent.lower():
            categories['research'] += 1
        else:
            categories['other'] += 1
    
    return categories


def generate_patterns_md(date: str, interactions: List[Dict]) -> str:
    """Generar archivo patterns.md."""
    top_phrases = extract_top_phrases(interactions)
    categories = classify_by_category(interactions)
    
    content = f"""# Patrones Recurrentes

**Fecha**: {date}  
**Total interacciones**: {len(interactions)}

---

## Frases/Elementos Más Empleados

| Elemento | Frecuencia |
|----------|------------|
"""
    
    for item, count in top_phrases[:10]:
        content += f"| {item} | {count} |\n"
    
    content += f"""
## Categorías por Tipo

| Categoría | Cantidad |
|-----------|----------|
"""
    
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            content += f"| {category.capitalize()} | {count} |\n"
    
    content += f"""
---

*Generado automáticamente por knowledge-indexer.py (BL-100)*
"""
    
    return content


def generate_trends_md(date: str, interactions: List[Dict]) -> str:
    """Generar archivo trends.md."""
    # Calcular actividad por hora
    hours = Counter()
    for interaction in interactions:
        timestamp = interaction.get('timestamp', '')
        if timestamp:
            try:
                hour = timestamp.split('T')[1].split(':')[0]
                hours[int(hour)] += 1
            except (IndexError, ValueError):
                pass
    
    # Tokens totales
    tokens_in = sum(i.get('tokens_in', 0) for i in interactions)
    tokens_out = sum(i.get('tokens_out', 0) for i in interactions)
    
    content = f"""# Tendencias de Uso

**Fecha**: {date}

---

## Actividad por Hora

| Hora | Interacciones |
|------|---------------|
"""
    
    for hour in sorted(hours.keys()):
        content += f"| {hour:02d}:00 | {hours[hour]} |\n"
    
    content += f"""
## Tokens Procesados

| Métrica | Cantidad |
|---------|----------|
| Input | {tokens_in:,} |
| Output | {tokens_out:,} |
| Total | {tokens_in + tokens_out:,} |

---

*Generado automáticamente por knowledge-indexer.py (BL-100)*
"""
    
    return content


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Knowledge Indexer - Genera insights automáticos')
    parser.add_argument('--date', type=str, help='Fecha específica (YYYY-MM-DD)')
    args = parser.parse_args()
    
    date = args.date or datetime.now().strftime('%Y-%m-%d')
    
    print(f"📊 Knowledge Indexer - {date}")
    print("=" * 50)
    
    # Leer interacciones
    interactions = read_interactions(date)
    print(f"   Leyendo interacciones: {len(interactions)} eventos")
    
    if not interactions:
        print("   ⚠️  No hay interacciones para esta fecha")
        return 0
    
    # Generar patterns.md
    patterns_content = generate_patterns_md(date, interactions)
    patterns_file = INSIGHTS_DIR / 'patterns.md'
    patterns_file.write_text(patterns_content, encoding='utf-8')
    print(f"   ✅ patterns.md generado")
    
    # Generar trends.md
    trends_content = generate_trends_md(date, interactions)
    trends_file = INSIGHTS_DIR / 'trends.md'
    trends_file.write_text(trends_content, encoding='utf-8')
    print(f"   ✅ trends.md generado")
    
    print(f"\n📁 Insights guardados en: {INSIGHTS_DIR}")
    print(f"\nPara ver resultados:")
    print(f"   cat {patterns_file}")
    print(f"   cat {trends_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

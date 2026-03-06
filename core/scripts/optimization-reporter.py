#!/usr/bin/env python3
"""
Optimization Reporter - PA Framework
====================================

Genera reporte de optimización al cierre de sesión.

Uso:
    python core/scripts/optimization-reporter.py           # Reporte del día
    python core/scripts/optimization-reporter.py --date=YYYY-MM-DD

Autor: FreakingJSON-PA Framework
Versión: 1.0.0 (BL-100)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONTEXT_DIR = REPO_ROOT / "core" / ".context"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
INTERACTIONS_DIR = KNOWLEDGE_DIR / "interactions"
INSIGHTS_DIR = KNOWLEDGE_DIR / "insights"
SESSIONS_DIR = CONTEXT_DIR / "sessions"

# Ensure directories exist
INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# Estimados de tiempo tradicional (en horas) por tipo de tarea
TIME_ESTIMATES = {
    'file_write': 0.5,      # 30 min por archivo
    'feature': 2.0,         # 2h por feature
    'bugfix': 1.0,          # 1h por bugfix
    'documentation': 0.5,   # 30 min por doc
    'prompt': 0.25,         # 15 min por prompt
}


def read_interactions(date: str) -> List[Dict]:
    """Leer interacciones del día."""
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


def count_sessions(date: str) -> int:
    """Contar sesiones del día."""
    session_file = SESSIONS_DIR / f"{date}.md"
    return 1 if session_file.exists() else 0


def calculate_time_saved(interactions: List[Dict], session_duration_hours: float = 1.0) -> float:
    """
    Calcular tiempo ahorrado.
    
    Fórmula: (tiempo_tradicional - tiempo_framework)
    
    tiempo_tradicional: Suma de estimados por tipo de tarea
    tiempo_framework: Duración real de la sesión
    """
    # Calcular tiempo tradicional estimado
    traditional_time = 0.0
    
    for interaction in interactions:
        event = interaction.get('event', '')
        
        # Estimar tiempo tradicional
        if event == 'file_write':
            traditional_time += TIME_ESTIMATES['file_write']
        elif event == 'prompt':
            traditional_time += TIME_ESTIMATES['prompt']
    
    # Tiempo framework (duración real)
    framework_time = session_duration_hours
    
    # Ahorro
    time_saved = max(0, traditional_time - framework_time)
    
    return round(time_saved, 2)


def generate_optimization_report(date: str, interactions: List[Dict]) -> str:
    """Generar reporte de optimización."""
    # Conteos básicos
    total_events = len(interactions)
    prompts = len([i for i in interactions if i.get('event') == 'prompt'])
    file_writes = len([i for i in interactions if i.get('event') == 'file_write'])
    
    # Tokens
    tokens_in = sum(i.get('tokens_in', 0) for i in interactions)
    tokens_out = sum(i.get('tokens_out', 0) for i in interactions)
    
    # Tiempo ahorrado (asumimos 1h de sesión real)
    time_saved = calculate_time_saved(interactions, session_duration_hours=1.0)
    
    # Generar recomendaciones
    recommendations = []
    if prompts > 20:
        recommendations.append("- Considerar cachear respuestas frecuentes")
    if file_writes > 10:
        recommendations.append("- Agrupar tareas de edición similares")
    if tokens_out > 50000:
        recommendations.append("- Revisar si prompts pueden ser más concisos")
    
    if not recommendations:
        recommendations.append("- ¡Buen trabajo! Optimización en línea")
    
    content = f"""# Reporte de Optimización

**Fecha**: {date}  
**Sesiones**: {count_sessions(date)}

---

## 📊 Métricas del Día

### Eventos

| Tipo | Cantidad |
|------|----------|
| Total | {total_events} |
| Prompts | {prompts} |
| File Writes | {file_writes} |

### Tokens

| Tipo | Cantidad |
|------|----------|
| Input | {tokens_in:,} |
| Output | {tokens_out:,} |
| **Total** | **{tokens_in + tokens_out:,}** |

### Tiempo

| Métrica | Valor |
|---------|-------|
| Framework (real) | ~1.0h |
| Tradicional (estimado) | ~{total_events * 0.3:.1f}h |
| **Ahorrado** | **{time_saved:.1f}h** |

---

## 🏆 Logros

- ✅ {prompts} prompts ejecutados
- ✅ {file_writes} archivos modificados
- ✅ {tokens_in + tokens_out:,} tokens procesados
- ✅ **{time_saved:.1f}h ahorradas** vs método tradicional

---

## 💡 Recomendaciones

{chr(10).join(recommendations)}

---

*Generado automáticamente por optimization-reporter.py (BL-100)*
"""
    
    return content


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimization Reporter - Reporte de optimización')
    parser.add_argument('--date', type=str, help='Fecha específica (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, help='Archivo de salida (default: optimization-report.md)')
    args = parser.parse_args()
    
    date = args.date or datetime.now().strftime('%Y-%m-%d')
    
    print(f"📊 Optimization Reporter - {date}")
    print("=" * 50)
    
    # Leer interacciones
    interactions = read_interactions(date)
    print(f"   Leyendo interacciones: {len(interactions)} eventos")
    
    if not interactions:
        print("   ⚠️  No hay interacciones para esta fecha")
        print("   💡 Ejecutar logging primero: /optimize")
        return 0
    
    # Generar reporte
    report_content = generate_optimization_report(date, interactions)
    
    output_file = args.output or (INSIGHTS_DIR / 'optimization-report.md')
    if isinstance(output_file, str):
        output_file = Path(output_file)
    
    output_file.write_text(report_content, encoding='utf-8')
    print(f"   ✅ optimization-report.md generado")
    
    # Mostrar resumen
    print(f"\n📁 Reporte guardado en: {output_file}")
    print(f"\nPara ver resultados:")
    print(f"   cat {output_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

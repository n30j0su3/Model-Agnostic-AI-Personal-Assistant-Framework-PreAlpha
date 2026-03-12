#!/usr/bin/env python3
"""
Dashboard Data Generator - FreakingJSON Framework
==================================================

Genera dashboard-data.js con datos incrustados para que dashboard.html
funcione con doble-click (file://) sin problemas de CORS.

Uso:
    python generate-dashboard-data.py

Output:
    dashboard-data.js - Archivo JavaScript con datos embebidos

Autor: FreakingJSON-PA Framework
Versión: 1.0.0 (Dashboard v2.0 - File:// Compatible)
"""

import json
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
KNOWLEDGE_DIR = REPO_ROOT / "core" / ".context" / "knowledge"
OUTPUT_FILE = REPO_ROOT / "dashboard-data.js"


def load_json_file(file_path: Path) -> dict:
    """Cargar archivo JSON de forma segura."""
    if not file_path.exists():
        print(f"   ⚠️  No encontrado: {file_path.name}")
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"   ⚠️  Error leyendo {file_path.name}: {e}")
        return {}


def generate_dashboard_data():
    """Generar dashboard-data.js con todos los índices."""
    print("\n[DATA] Dashboard Data Generator")
    print("=" * 60)
    
    # Cargar índices
    print("\nCargando indices...")
    sessions_data = load_json_file(KNOWLEDGE_DIR / "sessions-index.json")
    skills_data = load_json_file(KNOWLEDGE_DIR / "skills-index.json")
    agents_data = load_json_file(KNOWLEDGE_DIR / "agents-index.json")
    
    # Preparar datos para embedir
    dashboard_data = {
        "generatedAt": "2026-03-06T12:00:00Z",
        "version": "2.0.0",
        "sessions": sessions_data.get("sessions", []),
        "skills": skills_data.get("skills", []),
        "agents": agents_data.get("agents", [])
    }
    
    # Resumir
    print(f"\n   [SESSIONS] {len(dashboard_data['sessions'])}")
    print(f"   [SKILLS]   {len(dashboard_data['skills'])}")
    print(f"   [AGENTS]   {len(dashboard_data['agents'])}")
    
    # Generar JavaScript
    print("\nGenerando dashboard-data.js...")
    
    js_content = f"""// Dashboard Data - Generado automáticamente
// NO EDITAR - Este archivo se regenera con generate-dashboard-data.py
// Fecha: {dashboard_data["generatedAt"]}
// Versión: {dashboard_data["version"]}

window.DASHBOARD_DATA = {json.dumps(dashboard_data, indent=2, ensure_ascii=False)};

// Funciones de utilid ad para acceder a los datos
window.getDashboardData = function() {{
    return window.DASHBOARD_DATA;
}};

window.getSkillsCount = function() {{
    return window.DASHBOARD_DATA?.skills?.length || 0;
}};

window.getAgentsCount = function() {{
    return window.DASHBOARD_DATA?.agents?.length || 0;
}};

window.getSessionsCount = function() {{
    return window.DASHBOARD_DATA?.sessions?.length || 0;
}};

console.log('[Dashboard Data] Cargado: ' + 
    window.getSkillsCount() + ' skills, ' + 
    window.getAgentsCount() + ' agents, ' + 
    window.getSessionsCount() + ' sessions');
"""
    
    # Guardar archivo
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"\n[OK] Archivo generado: {OUTPUT_FILE}")
    print(f"   Tamano: {OUTPUT_FILE.stat().st_size:,} bytes")
    
    # Instrucciones
    print("\n" + "=" * 60)
    print("INSTRUCCIONES DE USO:")
    print("=" * 60)
    print("\n1. Incluir en dashboard.html (antes del script principal):")
    print('   <script src="dashboard-data.js"></script>')
    print("\n2. Abrir dashboard.html con doble-click (file://)")
    print("\n3. Los datos se cargaran automaticamente")
    print("\n4. Para actualizar datos, regenerar con:")
    print("   python generate-dashboard-data.py")
    print("\n" + "=" * 60)
    
    return dashboard_data


if __name__ == '__main__':
    generate_dashboard_data()

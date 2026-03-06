// Dashboard Data - Generado automáticamente
// NO EDITAR - Este archivo se regenera con generate-dashboard-data.py
// Fecha: 2026-03-06T12:00:00Z
// Versión: 2.0.0

window.DASHBOARD_DATA = {
  "generatedAt": "2026-03-06T12:00:00Z",
  "version": "2.0.0",
  "sessions": [
    {
      "id": "2026-03-06",
      "title": "Sesión 2026-03-06",
      "date": "2026-03-06",
      "startTime": "08:01",
      "summary": "Sesión de ejecución completa. Plan de 5 tareas críticas aprobado y ejecutado exitosamente. Framework ahora tiene:\n- Comandos slash compatibles con OpenCode CLI oficial\n- Knowledge Base estructurada pa",
      "topics": [
        "Inicialización de sesión 2026-",
        "Lectura de contexto base: `cor",
        "Planificación de 5 tareas crít",
        "Ejecución completa del plan ap"
      ],
      "type": "release",
      "stats": {
        "word_count": 495,
        "lines": 93,
        "decisions": 1,
        "pending": 0,
        "completed": 0
      },
      "sessionFile": "core/.context/sessions/2026-03-06.md"
    }
  ],
  "skills": [
    {
      "name": "Content Optimizer",
      "displayName": "@Content Optimizer",
      "description": "Optimiza borradores de texto para SEO, legibilidad y engagement. Ajusta el tono de voz y la estructura del contenido. Usalo en el workspace @content.",
      "category": "content",
      "location": "core/skills/core/content-optimizer/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [
        "@archivo\""
      ],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "Context Evaluator",
      "displayName": "@Context Evaluator",
      "description": "Framework para evaluar la calidad de las respuestas de los agentes mediante el patron \"LLM-as-a-Judge\". Permite comparacion de respuestas y evaluacion contra rubricas.",
      "category": "core",
      "location": "core/skills/core/context-evaluator/",
      "skillFile": "SKILL.md",
      "examples": [
        "python core/skills/core/context-evaluator/scripts/evaluate.py --prompt \"...\" --response \"...\" --rubric general"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "Decision Engine",
      "displayName": "@Decision Engine",
      "description": "Evalua instrucciones con enfoque local-first y decide entre ejecucion local, delegacion a agentes o uso de LLM remoto. Usalo para optimizar contexto, cuota y resultados.",
      "category": "core",
      "location": "core/skills/core/decision-engine/",
      "skillFile": "SKILL.md",
      "examples": [
        "python core/skills/core/decision-engine/scripts/route.py \"texto del usuario\""
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "MCP Builder",
      "displayName": "@MCP Builder",
      "description": "Guides creation of MCP servers with strong tool design, schemas, and evaluation practices.",
      "category": "core",
      "location": "core/skills/core/mcp-builder/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "Paper Summarizer",
      "displayName": "@Paper Summarizer",
      "description": "Analiza y resume documentos tecnicos, papers cientificos o articulos extensos. Extrae metodologia, hallazgos clave y conclusiones. Usalo en el workspace @research.",
      "category": "research",
      "location": "core/skills/core/paper-summarizer/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [
        "@archivo\""
      ],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "Skill Discovery Helper",
      "displayName": "@Skill Discovery Helper",
      "description": "Helper para identificar skills apropiadas para tareas comunes y evitar crear scripts innecesarios",
      "category": "core",
      "location": "core/skills/core/skill-discovery/",
      "skillFile": "SKILL.md",
      "examples": [
        "read: core/skills/core/{nombre}/SKILL.md",
        "@skill-name\n\n\"Usa @csv-processor para limpiar este archivo CSV\""
      ],
      "commands": [
        "@xlsx | `core/skills/core/xlsx/` | Crear hojas de cálcul",
        "@etl | `core/skills/core/etl/` | ETL: Extract, Transfor"
      ],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "atribucion",
      "displayName": "@atribucion",
      "description": "Skill para analisis de metricas de atribucion por canal. Procesa Excel, calcula metricas (RPS, CR) y genera reportes HTML con variacion semanal.",
      "category": "maaji",
      "location": "core/skills/local/atribucion/",
      "skillFile": "SKILL.md",
      "examples": [
        "cd workspaces/professional/projects/Maaji/Automatizaciones/DEV/atribucion\n\n# Ejecutar flujo completo\npython scripts/generar_reportes_fix.py"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active",
      "workspace": "maaji"
    },
    {
      "name": "checkout-con-evento",
      "displayName": "@checkout-con-evento",
      "description": "Skill para generar analisis de checkout CR con evento comercial. Lee datos raw centralizados en Maaji y genera dashboard con analisis de impacto.",
      "category": "maaji",
      "location": "core/skills/local/checkout-con-evento/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [],
      "whenToUse": [],
      "status": "active",
      "workspace": "maaji"
    },
    {
      "name": "checkout-sin-evento",
      "displayName": "@checkout-sin-evento",
      "description": "Skill para generar analisis de checkout CR sin evento comercial. Lee datos raw centralizados en Maaji, procesa con Python y genera dashboard HTML + analisis Markdown.",
      "category": "maaji",
      "location": "core/skills/local/checkout-sin-evento/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [],
      "whenToUse": [],
      "status": "active",
      "workspace": "maaji"
    },
    {
      "name": "csv-processor",
      "displayName": "@csv-processor",
      "description": "Procesa archivos CSV para limpieza, transformación y análisis de datos tabulares. Esta skill debe usarse cuando el usuario necesite manipular datos CSV, incluyendo limpieza de datos, transformaciones (filtros, agregaciones, joins), conversión a otros formatos, o análisis exploratorio de datasets en formato CSV.",
      "category": "core",
      "location": "core/skills/core/csv-processor/",
      "skillFile": "SKILL.md",
      "examples": [
        "### Ejemplo 1: Limpieza Básica",
        "python core/skills/core/csv-processor/scripts/csv_processor.py \\",
        "CSV sucio → @csv-processor (limpieza) → @xlsx (formateo) → @docx (reporte)"
      ],
      "commands": [
        "@etl para pipelines ETL multi-formato |",
        "@xlsx |"
      ],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "data-viz",
      "displayName": "@data-viz",
      "description": "Genera visualizaciones de datos (gráficos de barras, líneas, etc.) usando Matplotlib y Seaborn.",
      "category": "Data",
      "location": "core/skills/core/data-viz/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "docx",
      "displayName": "@docx",
      "description": "Comprehensive document creation, editing, and analysis with support for tracked changes, formatting preservation, and text extraction. Use when working with Word documents (.docx).",
      "category": "core",
      "location": "core/skills/core/docx/",
      "skillFile": "SKILL.md",
      "examples": [
        "pandoc --track-changes=all document.docx -o output.md",
        "python scripts/unpack.py document.docx ./unpacked"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "etl",
      "displayName": "@etl",
      "description": "Sin descripción",
      "category": "core",
      "location": "core/skills/core/etl/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "json-prompt-generator",
      "displayName": "@json-prompt-generator",
      "description": "Genera prompts JSON estructurados a partir de una idea inicial para IA, con objetivos y entregables claros.",
      "category": "core",
      "location": "core/skills/core/json-prompt-generator/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "klaviyo-extract",
      "displayName": "@klaviyo-extract",
      "description": "Skill para extraer datos de Klaviyo (segments, lists, campaigns) usando MCP tools. Soporta empresas INT y COL. Ejecuta desde BASE/klaviyo-extract/.",
      "category": "maaji",
      "location": "core/skills/local/klaviyo-extract/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [],
      "whenToUse": [],
      "status": "active",
      "workspace": "maaji"
    },
    {
      "name": "markdown-writer",
      "displayName": "@markdown-writer",
      "description": "Guía para escribir documentación Markdown de alta calidad siguiendo el principio MVI del framework FreakingJSON. Esta skill debe usarse cuando el usuario necesite crear o editar archivos .md en el framework, asegurando consistencia, claridad y adherencia al principio de Minimal Viable Information.",
      "category": "core",
      "location": "core/skills/core/markdown-writer/",
      "skillFile": "SKILL.md",
      "examples": [
        "### Ejemplo 1: Crear Sesión Diaria",
        "## Ejemplos\n\n### Ejemplo 1: Crear Sesión Diaria"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "pdf",
      "displayName": "@pdf",
      "description": "Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. Use when the user needs to process or generate PDF files.",
      "category": "core",
      "location": "core/skills/core/pdf/",
      "skillFile": "SKILL.md",
      "examples": [
        "import pdfplumber\nwith pdfplumber.open(\"doc.pdf\") as pdf:\n    table = pdf.pages[0].extract_table()",
        "from reportlab.pdfgen import canvas\nc = canvas.Canvas(\"hello.pdf\")\nc.drawString(100, 750, \"Hello World\")\nc.save()"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "pptx",
      "displayName": "@pptx",
      "description": "Presentation creation, editing, and analysis with support for layouts, notes, and design. Use when working with PowerPoint files (.pptx).",
      "category": "core",
      "location": "core/skills/core/pptx/",
      "skillFile": "SKILL.md",
      "examples": [
        "python -m markitdown presentation.pptx > content.md",
        "python scripts/thumbnail.py presentation.pptx ./output"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "prd-generator",
      "displayName": "@prd-generator",
      "description": "Generates structured Product Requirements Documents with user stories, acceptance criteria, and stakeholder alignment.",
      "category": "core",
      "location": "core/skills/core/prd-generator/",
      "skillFile": "SKILL.md",
      "examples": [
        "As a [user type]\nI want to [action]\nSo that [benefit]",
        "Given [context]\nWhen [action]\nThen [expected result]"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "prompt-improvement",
      "displayName": "@prompt-improvement",
      "description": "Mejora prompts con estandares modernos (RAG, few-shot, JSON prompts) y criterios de calidad. Usalo en el workspace @development.",
      "category": "core",
      "location": "core/skills/core/prompt-improvement/",
      "skillFile": "SKILL.md",
      "examples": [
        "{\n  \"task\": \"\",\n  \"context\": \"\",\n  \"inputs\": [],\n  \"constraints\": [],\n  \"output_format\": \"\",\n  \"quality_checks\": []\n}"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "python-standards",
      "displayName": "@python-standards",
      "description": "Estándares y validación para scripts Python cross-platform (Windows/Linux/macOS). Esta skill debe usarse cuando se escriban scripts Python en el framework para garantizar compatibilidad multi-SO, evitar problemas de encoding (emojis en Windows), y asegurar calidad consistente en todo el código.",
      "category": "core",
      "location": "core/skills/core/python-standards/",
      "skillFile": "SKILL.md",
      "examples": [
        "UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f680'"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "skill-creator",
      "displayName": "@skill-creator",
      "description": "Guía completa para crear nuevas skills en el framework FreakingJSON. Use cuando el usuario quiera crear, actualizar o empaquetar una skill que extienda las capacidades del asistente con conocimiento especializado, workflows o integraciones de herramientas.",
      "category": "core",
      "location": "core/skills/core/skill-creator/",
      "skillFile": "SKILL.md",
      "examples": [
        "# Código de ejemplo si aplica",
        "python core/skills/core/skill-creator/scripts/init_skill.py <nombre-skill> --path <directorio-salida>",
        "python core/skills/core/skill-creator/scripts/package_skill.py <ruta/a/skill-folder>"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "task-management",
      "displayName": "@task-management",
      "description": "Sistema avanzado de gestión de tareas multidisciplinarias. Permite crear, categorizar por workspace y mover tareas entre archivos de contexto y la sesión actual.",
      "category": "core",
      "location": "core/skills/core/task-management/",
      "skillFile": "SKILL.md",
      "examples": [],
      "commands": [
        "@workspace #prioridad`"
      ],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "ui-ux-pro-max",
      "displayName": "@ui-ux-pro-max",
      "description": "UI/UX design intelligence with searchable database",
      "category": "core",
      "location": "core/skills/core/ui-ux-pro-max/",
      "skillFile": "SKILL.md",
      "examples": [
        "python3 --version || python --version",
        "brew install python3",
        "sudo apt update && sudo apt install python3"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    },
    {
      "name": "xlsx",
      "displayName": "@xlsx",
      "description": "Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. Use when working with .xlsx, .csv, .tsv files.",
      "category": "core",
      "location": "core/skills/core/xlsx/",
      "skillFile": "SKILL.md",
      "examples": [
        "import pandas as pd\ndf = pd.read_excel('file.xlsx')\ndf.head()\ndf.to_excel('output.xlsx', index=False)",
        "python scripts/recalc.py <excel_file> [timeout_seconds]"
      ],
      "commands": [],
      "whenToUse": [],
      "status": "active"
    }
  ],
  "agents": [
    {
      "id": "FreakingJSON-PA",
      "name": "FreakingJSON-PA",
      "type": "core",
      "description": "Agente principal del Personal Assistant Framework en modo producción. Gestiona sesiones, contexto y delegación a subagentes para usuarios finales.",
      "purpose": "Gestión de tareas del framework",
      "whenToUse": [],
      "syntax": "@freakingjson-pa",
      "location": "core/agents/pa-assistant.md",
      "status": "operativo",
      "dependencies": []
    },
    {
      "id": "ContextScout",
      "name": "ContextScout",
      "type": "subagent",
      "description": "Todo el detalle de detección",
      "purpose": "Gestión de tareas del framework",
      "whenToUse": [],
      "syntax": "@contextscout",
      "location": "core/agents/subagents\\context-scout-v2.md",
      "status": "operativo",
      "dependencies": []
    },
    {
      "id": "ContextScout",
      "name": "ContextScout",
      "type": "subagent",
      "description": "Descubre y recomienda archivos de contexto desde core/.context/ ordenados por prioridad. Agente read-only.",
      "purpose": "Gestión de tareas del framework",
      "whenToUse": [],
      "syntax": "@contextscout",
      "location": "core/agents/subagents\\context-scout.md",
      "status": "operativo",
      "dependencies": []
    },
    {
      "id": "DocWriter",
      "name": "DocWriter",
      "type": "subagent",
      "description": "Genera documentación de sesiones, hallazgos y conocimiento siguiendo el principio MVI.",
      "purpose": "Gestión de tareas del framework",
      "whenToUse": [],
      "syntax": "@docwriter",
      "location": "core/agents/subagents\\doc-writer.md",
      "status": "operativo",
      "dependencies": []
    },
    {
      "id": "FeatureArchitect",
      "name": "FeatureArchitect",
      "type": "subagent",
      "description": "Arquitecto de producto y guardián de la filosofía. Evalúa, planea y ejecuta features del backlog con enfoque user-friendly y sin solapamientos.",
      "purpose": "Gestión de tareas del framework",
      "whenToUse": [],
      "syntax": "@featurearchitect",
      "location": "core/agents/subagents\\feature-architect.md",
      "status": "operativo",
      "dependencies": []
    },
    {
      "id": "SessionManager",
      "name": "SessionManager",
      "type": "subagent",
      "description": "Gestiona sesiones diarias: crea, actualiza y cierra sesiones en core/.context/sessions/.",
      "purpose": "Gestión de tareas del framework",
      "whenToUse": [],
      "syntax": "@sessionmanager",
      "location": "core/agents/subagents\\session-manager.md",
      "status": "operativo",
      "dependencies": []
    }
  ]
};

// Funciones de utilid ad para acceder a los datos
window.getDashboardData = function() {
    return window.DASHBOARD_DATA;
};

window.getSkillsCount = function() {
    return window.DASHBOARD_DATA?.skills?.length || 0;
};

window.getAgentsCount = function() {
    return window.DASHBOARD_DATA?.agents?.length || 0;
};

window.getSessionsCount = function() {
    return window.DASHBOARD_DATA?.sessions?.length || 0;
};

console.log('[Dashboard Data] Cargado: ' + 
    window.getSkillsCount() + ' skills, ' + 
    window.getAgentsCount() + ' agents, ' + 
    window.getSessionsCount() + ' sessions');

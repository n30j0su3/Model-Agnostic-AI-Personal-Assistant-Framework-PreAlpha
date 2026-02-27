# Backlog del Framework

Ultima actualizacion: 2026-01-30

## Versionado

- Estandar: SemVer (MAJOR.MINOR.PATCH) + Etiqueta de Ciclo de Vida (Alpha/Beta/RC/Stable).
- Al agregar caracteristicas: incrementa MINOR.
- Al corregir bugs: incrementa PATCH.
- Cambios incompatibles: incrementa MAJOR.
- **Etiquetado de Etapas (2026 Standard)**:
  - `Alpha`: Desarrollo core inestable.
  - `Beta`: Feature freeze, pulido UX.
  - `RC`: Candidato a estable.
  - `Stable`: Version oficial de produccion.
- Siempre actualiza el badge de version en `README.md` y este historial.

## Historial de cambios

- 2026-01-28: Se agregaron items BL-101 a BL-108 (Onboarding, ETL, Knowledge Base, Research, Dev/Agent, Console Agent, Quotas).
- 2026-01-30: Migración masiva de estado y adición de columna Workspace (BL-118). Implementación de CORE-VITALS Batch 1.
- 2026-01-28: Se actualizo BL-050 (config autom), BL-090 (skillful optimization) y BL-094 (toon core-skill).
- 2026-01-27: Alineacion con SRLC (Etapa Alpha declarada). Reporte de analisis externo de Agent-Skills integrado.
- 2026-01-27: Se agregaron items BL-091 a BL-095.
- 2026-01-27: Se marco BL-068 como Hecho.

 | ID | Item | Prioridad | Estado | Workspace | Criterios de aceptacion | 
| --- | --- | --- | --- | --- | --- |
 | BL-001 | Guia "para dummies" con prerequisitos de hardware y software | Alta | Hecho | Development | README incluye requisitos claros y un paso a paso de instalacion completa | 
 | BL-002 | Instalacion de LLMs (IA) paso a paso | Alta | Hecho | Development | README detalla cuentas, API keys, configuracion y validacion basica | 
 | BL-003 | Instalador todo-en-uno en comando unico | Alta | Hecho | Development | README incluye un comando para Windows y otro para macOS/Linux | 
 | BL-004 | FAQ basico para usuarios no tecnicos | Alta | Hecho | Development | README incluye al menos 5 preguntas frecuentes con respuestas cortas | 
 | BL-005 | Frase insignia en README | Media | Hecho | Development | La frase aparece en la introduccion del README | 
 | BL-006 | Agradecimientos formales en README | Media | Hecho | Development | Se incluye seccion de agradecimientos con el texto solicitado | 
 | BL-007 | Skill json-prompt-generator | Alta | Hecho | Development | Skill creado en `skills/core/json-prompt-generator` con instrucciones y ejemplo | 
 | BL-008 | Orquestacion multi-modelo con conmutacion rapida | Alta | Hecho | Development | Flujo unificado documentado para OpenCode, Claude, Gemini y Codex | 
 | BL-009 | Gestion de contexto local versionado | Alta | Hecho | Development | Estructura `.context/` definida y versionada sin lock-in | 
 | BL-010 | Workspaces multidisciplinarios aislados | Media | Pendiente | Development | Workspaces claramente separados por disciplina y documentados | 
 | BL-011 | Sistema de agentes especializados con roles claros | CORE VITALS | Hecho | Development | Catalogo de agentes con responsabilidades y uso recomendado | 
 | BL-012 | Skills modulares para tareas recurrentes | CORE VITALS | Hecho | Development | Libreria de skills con index y versionado actualizado | 
 | BL-013 | Trazabilidad diaria automatica | CORE VITALS | Hecho | Development | Sesiones diarias registradas y accesibles desde `sessions/`. Dependencias: BL-014 | 
 | BL-014 | Pipeline de sincronizacion coherente | CORE VITALS | Hecho | Development | Script de sync mantiene coherencia entre herramientas e incluye automatizaciones en `scripts/` | 
 | BL-015 | Documentacion integrada estilo Mintlify | Baja | Pendiente | Development | Docs consistentes y navegables en `docs/` | 
 | BL-016 | Estructura de carpetas estable y extensible | CORE VITALS | Hecho | Development | Convenciones de nombres y ubicaciones estandarizadas | 
 | BL-017 | Scripts de automatizacion para sync y normalizacion | N/A | N/A | Development | Unificado con BL-014 | 
 | BL-018 | Compatibilidad multiplataforma | CORE VITALS | Delegado | Development | Rutas y comandos probados en Windows/macOS/Linux | 
 | BL-019 | Diseno de interfaz soportado por skill UI/UX | CORE VITALS | Delegado | Content | Skill UI/UX disponible y referenciado en docs | 
 | BL-020 | Revisar jerarquia de scopes (agents/skills/workspaces) | Media | Hecho | Development | Backlog borrador local con sugerencias en `docs/backlog.local.md` | 
 | BL-021 | Agregar skill prd-generator | Alta | Hecho | Development | Skill creado en `skills/core/prd-generator` y listado en el indice | 
 | BL-022 | Agregar skill mcp-builder | Alta | Hecho | Development | Skill creado en `skills/core/mcp-builder` y listado en el indice | 
 | BL-023 | Evaluar skill docker-claude-skill | Baja | Pendiente | Development | Fuente: https://github.com/wrsmith108/docker-claude-skill | 
 | BL-024 | Evaluar skill claude-skill-version-sync | Baja | Pendiente | Development | Fuente: https://github.com/wrsmith108/claude-skill-version-sync | 
 | BL-025 | Evaluar skill claude-skill-docker-optimizer | Baja | Pendiente | Development | Fuente: https://github.com/wrsmith108/claude-skill-docker-optimizer | 
 | BL-026 | Evaluar skill RchGrav-claudebox | Baja | Pendiente | Development | Fuente: https://agent-skills.cc/skills/RchGrav-claudebox | 
 | BL-027 | Evaluar skill vibe-to-docker | Baja | Pendiente | Development | Fuente: https://github.com/wrsmith108/vibe-to-docker | 
 | BL-028 | Documentar jerarquia de scopes en docs | Media | Hecho | Development | Documento creado en `docs/architecture/scopes.mdx` | 
 | BL-029 | Selector de instalacion basica vs pro | Alta | Hecho | Development | Instalador ofrece seleccion de perfil en primera ejecucion | 
 | BL-030 | Configuracion guiada del perfil al instalar | Alta | Hecho | Development | Permite configurar `.context/MASTER.md` ahora o despues con preferencias avanzadas opcionales | 
 | BL-031 | Agregar workspace Homelab | Alta | Hecho | Development | Workspace creado y documentado en `workspaces/homelab/` | 
 | BL-032 | Plantillas Homelab (inventario, servicios, mantenimiento) | Baja | Pendiente | Development | Plantillas listas para completar en `workspaces/homelab/` | 
 | BL-033 | Integrar contexto “user-friendly” al inicio del README | Alta | Hecho | Development | README incluye el texto completo sobre “sin MIEDO” y paradigma AI/IA | 
 | BL-034 | Sistema de calendario, control y estimacion de actividades | Media | Pendiente | Development | Integra skills/tecnologias open-source y evalua integracion con Google/Outlook | 
 | BL-035 | Sistema de entrada multi-canal de ideas/tareas/objetivos | Media | Pendiente | Development | Ingreso via WhatsApp/Telegram con clasificacion por workspace y deteccion de recursos faltantes; contexto guardado en .md | 
 | BL-036 | Integrar skill writing-style | Baja | Pendiente | Development | Skill integrada desde https://github.com/jrenaldi79/writing-style | 
 | BL-037 | Integrar skill agentman-social-media con tono configurable | Baja | Pendiente | Development | Skill integrada y permite elegir tono/intencion acorde al contexto | 
 | BL-038 | Integrar skill running-marketing-campaigns-agent-skill | Baja | Pendiente | Development | Skill integrada desde https://github.com/SpillwaveSolutions/running-marketing-campaigns-agent-skill | 
 | BL-039 | Panel de control global para configuraciones | Alta | Hecho | Development | Script `scripts/pa.py` permite gestionar sincronizacion, preferencias, orquestacion y launcher | 
 | BL-040 | Documentar dashboard.html en README | Alta | Hecho | Development | Seccion Documentacion incluye proposito y uso de `dashboard.html` | 
 | BL-041 | Agradecimientos a NetworkChuck | Alta | Hecho | Development | Seccion de agradecimientos menciona a NetworkChuck con cita | 
 | BL-042 | Modulo de pruebas del framework configurable | Media | Pendiente | Development | Sistema de pruebas ajustado a preferencias del usuario para validar el framework | 
 | BL-043 | Seccion rapida de caracteristicas (dogfooding, backlog y despliegue seguro) | Alta | Hecho | Development | Cada seccion revisa backlog, documenta cambios, usa el framework y valida privacidad antes de deploy | 
 | BL-044 | Integrar skill de prompt-improvement con estandares modernos | Alta | Hecho | Development | Skill con buenas practicas (CoT, RAG, few-shot, JSON prompts), referencias confiables y actualizacion programable por usuario | 
 | BL-045 | Planear framework/skill de investigacion multiproposito | Alta | Pendiente | Development | Skill global con modos de investigacion (sencilla, deep-research, profesional) y flujo guiado opcional | 
 | BL-046 | Integrar desinstalador del framework (completo o parcial) | Alta | Hecho | Development | Proceso seguro de desinstalacion documentado y con opcion parcial | 
 | BL-047 | TaskManager para programar mantenimiento y automatizaciones | CORE VITALS | Hecho | Development | Sistema implementado en scripts/pa.py con verificacion de 30 dias | 
 | BL-048 | Planear/Integrar script de mantenimiento del framework (cada 30 dias) | N/A | N/A | Development | Unificado con BL-047 | 
 | BL-049 | Planear/Integrar script de verificacion de jerarquia y overlaps | N/A | N/A | Development | Unificado con BL-069 | 
 | BL-050 | Guia de obtencion de API keys (OpenAI/Gemini/Claude/OpenRouter) | Alta | Pendiente | Development | Docs para OpenAI, Gemini, Claude, OpenRouter y similares con pasos claros. Incluir guia/proceso de configuracion automatica en installer/dashboard (ref: opencode-antigravity-auth). | 
 | BL-051 | Mantener `dashboard.html` actualizado | Alta | Pendiente | Development | `dashboard.html` siempre actualizado, con enlaces internos/externos y narrativa completa. Insumos: BL-043, BL-040 | 
 | BL-052 | Integrar marca "FreakingJSON" (ASCII/Metadata/Theme) | Media | Pendiente | Development | Integrar "FreakingJSON" en instaladores (ASCII alta compatibilidad), docs y metadatos por defecto. Usar estandares opensource actuales para colores/personalizacion user-friendly | 
 | BL-053 | Crear themes de personalizacion por workspaces y agentes | Media | Pendiente | Development | Temas seleccionables con buenas practicas y guia de uso. Dependencias: BL-052 | 
 | BL-054 | Planear sistema de plugins para expandir capacidades del framework | Media | Pendiente | Development | Arquitectura de plugins basada en estandares opensource actualizados | 
 | BL-055 | Planear skills de video editing/creacion opensource | Baja | Pendiente | Development | Roadmap de skills con herramientas como FFmpeg y NCA-Toolkit | 
 | BL-056 | Planear skill de automatizacion de contenido multiplataforma | Baja | Pendiente | Development | Automatizacion con noticias, videos, transcripciones, TTS, imagenes y APIs | 
 | BL-057 | Planear skill/framework para romhacks multiplataforma | Baja | Pendiente | Development | Flujo de edicion, parcheo y build con recursos opensource y docs publicas | 
 | BL-058 | Integrar tips rapidos/recomendados de uso del framework | N/A | N/A | Development | Unificado con BL-081 | 
 | BL-059 | Actualizacion automatica del framework (configurable/programable) | Alta | Hecho | Development | Script de actualizacion con fallback sin Git y opcion en pa.py | 
 | BL-060 | CORE SKILL de evaluacion/decision de instrucciones (local-first) | CORE VITALS | Hecho | Development | Skill creada en `skills/core/decision-engine` con router local-first, reglas y delegacion. Plan tecnico en `docs/architecture/decision-engine.mdx` | 
 | BL-061 | Historico de contexto configurable (online/local) | Media | Hecho | Development | Usuario puede elegir entre sincronizacion online (GitHub) o local para historicos y contexto, reduciendo barreras de entrada | 
 | BL-062 | Unificado con BL-050 | N/A | N/A | Development | La tarea de documentar tutoriales de API Keys se fusiona con el item existente BL-050 | 
 | BL-063 | Setup inteligente de repositorio (GitHub/local/sandbox) | Alta | Hecho | Development | Flujo interactivo en el instalador con cascada gh -> PyGithub -> API nativa | 
 | BL-064 | Selector de idioma ES/EN en instalador y panel | Alta | Hecho | Development | Framework permite elegir idioma y usa strings centralizados en config/i18n.json | 
 | BL-065 | Seleccion de CLI por defecto + asistencia de instalacion | Alta | Hecho | Development | Instalador detecta CLIs, permite elegir default y ofrece instalar OpenCode | 
 | BL-066 | Inicializacion robusta de contexto IA | Alta | Hecho | Development | .cursorrules y AI_INSTRUCTIONS.md apuntan a .context/ y launcher imprime prompt magico | 
 | BL-067 | Auditoria UX end-to-end (instaladores, mensajes y docs) | Alta | Pendiente | Development | Experiencia guiada, clara y amigable para usuarios no tecnicos en instalacion, actualizacion y uso inicial | 
 | BL-068 | Agent @feature-architect para Feature Sessions | CORE VITALS | Hecho | Development | Agent creado con bootstrap, clarificacion, evaluacion, ejecucion y herramienta de backlog compatible | 
 | BL-068.1 | Definir interfaz estable para conflict-guard | CORE VITALS | Hecho | Development | Inputs/outputs documentados, compatibles con validacion automatica y reutilizables por agents/skills | 
 | BL-068.2 | Event schema para integracion session-manager + task-management | CORE VITALS | Hecho | Development | Esquema de eventos documentado con ejemplos y uso en logs/tareas | 
 | BL-068.3 | Formato estandar de Feature Analysis Report | CORE VITALS | Hecho | Development | Plantilla compacta reusable con secciones de scope, overlaps, decisiones y riesgos | 
 | BL-069 | CORE-LOGIC: validar overlaps/conflictos al integrar skills/dependencias | CORE VITALS | Hecho | Development | Feature-architect verifica rutas y conflictos funcionales antes de integrar una nueva feature. Incluye verificacion periodica (script) y dependencias: BL-068 | 
 | BL-070 | Evaluar skills ralph/prd para reforzar agente feature-architect | Alta | Hecho | Development | Comparativa e integracion solo si mejora robustez segun estandares actuales. Dependencias: BL-068 | 
 | BL-071 | Evaluar skills session-logs/context-files/multi-tool para session-manager | CORE VITALS | Hecho | Development | Integracion si aporta mejoras verificables y compatibles. Dependencias: BL-060 | 
 | BL-072 | Evaluar si session-tracking debe integrarse en session-manager | CORE VITALS | Hecho | Development | Decision documentada y criterio alineado a la filosofia del framework. Dependencias: BL-060 | 
 | BL-073 | Evaluar skills git/github para mejorar github-deployer | CORE VITALS | Hecho | Development | Integracion si aporta mejoras verificables y compatibles. Dependencias: BL-060 | 
 | BL-074 | Implementar core-skill de data visualization (Seaborn/Matplotlib) | Alta | Pendiente | Development | Skill documentada y alineada a estandares opensource actuales | 
 | BL-075 | Implementar core-skill "council of the wise" | Alta | Pendiente | Development | Skill integrada desde fuente indicada y documentada | 
 | BL-076 | Integrar summarize + transcript-to-content (sin referencia a clawdbot) | Media | Pendiente | Development | Skills integradas sin referencia directa a clawdbot en docs, incluye transcripcion de contenido | 
 | BL-077 | Implementar core-skill de transcripcion de contenido | N/A | N/A | Development | Unificado con BL-076 | 
 | BL-078 | Evaluar/Integrar skill/agent Google Workspace (No Cloud Console) | Media | Pendiente | Development | Opcion para Gmail/Calendar/Drive/Docs/Sheets documentada | 
 | BL-079 | Instalador: ofrecer instalar CLI elegido o guiar instalacion (pa.bat) | CORE VITALS | Pendiente | Development | Opcion en instalador con links internos/externos | 
 | BL-080 | Integrar buenas practicas de uso Gemini (docs) | Alta | Pendiente | Development | Guia basada en la doc indicada y adaptada al framework. Dependencias: BL-050 | 
 | BL-081 | Integrar referencias de cheat-sheet/troubleshooting y tips rapidos | CORE VITALS | Pendiente | Development | Docs y dashboard incluyen seccion de tips rapidos y referencias relevantes | 
 | BL-082 | Integrar gestor/banco de skills instalables | Alta | Pendiente | Development | Sistema para buscar/instalar skills sin conflictos ni overlaps | 
 | BL-083 | Acceso a documentacion local del framework | Baja | Hecho | Development | Cockpit carga docs locales con manifest (`docs/docs_manifest.js`) y visor integrado | 
 | BL-084 | Vendoring de assets offline para docs/cockpit | CORE VITALS | Hecho | Development | Assets locales en `docs/lib/` y script de descarga `scripts/vendor_assets.py` | 
 | BL-085 | UX docs/dashboard no tecnico (sin dependencias extra) | CORE VITALS | Hecho | Development | Dashboard ofrece opciones claras, abre archivos sin confusion y funciona en navegador sin requerir Python o instalaciones ocultas | 
 | BL-086 | Historial de interacciones locales para consulta y reutilizacion | CORE VITALS | Pendiente | Development | Interacciones guardadas localmente en formato estructurado, consultables por skill/agent, opcion on/off y documentado | 
 | BL-087 | Agents.md en raiz para guiar inicializacion segura | CORE VITALS | Hecho | Development | Archivo en raiz evita sobreescrituras, redirige a `.context/` y define flujo de inicializacion | 
 | BL-088 | Renombrar nombre de sesion/ventana/contexto/chat con el nombre del Framework tras inicializacion (pa.bat, pa.sh, zip directo, etc.) | Baja | Pendiente | Development | Al inicializar el framework, el titulo/identificador de la sesion/ventana/contexto/chat usa el nombre del Framework. Cubre pa.bat, pa.sh, instalacion zip directa y cualquier metodo documentado. No rompe CLIs y es local-first. | 
 | BL-089 | Auditar sesiones recientes para identificar prompts/roles/agentes reutilizables e integrar mejoras | Alta | Pendiente | Development | Revisar ultimas sesiones en sessions/, documentar hallazgos, proponer integraciones o mejoras y actualizar backlog con decisiones. | 
 | BL-090 | Evaluar plugin @zenobius/opencode-skillful | Baja | Pendiente | Development | Verificar uso en repo/config, buscando aprovechar caracteristicas de optimizacion/seguridad/ahorro de recursos. Garantizar maxima compatibilidad (Opencode CLI default) y decidir integrar o descartar con justificacion. | 
 | BL-091 | Sistema de logging de prompts ejecutados | CORE VITALS | Delegado | Development | Registra prompts/roles/agent/skill en JSONL local. Delegado a Codex. | 
 | BL-092 | Tracking real de tokens y API calls | CORE VITALS | Delegado | Development | Registra tokens de entrada/salida y costos estimados. Delegado a Codex. | 
 | BL-093 | Cache L1/L2/L3 de contexto (OmniMemory pattern) | Alta | Hecho | Development | Implementada Skill OmniMemory con estructura L1 (temp), L2 (sessions/thinking.jsonl) y L3 (memory.md). Orchestrator registra thinking. | 
 | BL-094 | TOON encoder para datos tabulares | Alta | Pendiente | Development | Core-Skill basado en https://github.com/toon-format/toon, similar a json-prompt-generator, para conversion de tablas a formato TOON con ejemplo y docs. | 
 | BL-095 | Orquestador inteligente de tareas y delegacion | Alta | Hecho | Development | Orquestador que clasifica tareas, delega a agents/skills y retorna resumen, documentado y sin lock-in. | 
 | BL-096 | Implementar "Progressive Disclosure" en @orchestrator | Alta | Hecho | Development | El orquestador carga solo metadatos de agentes y lee AGENT.md completo solo bajo demanda para ahorrar tokens. | 
 | BL-097 | Crear core-skill "context-evaluator" (LLM-as-a-Judge) | Media | Hecho | Development | Framework de evaluacion automatica de respuestas basado en rubricas y comparacion pairwise. | 
 | BL-098 | Implementar "Context Compaction" en session-manager | Media | Hecho | Development | Algoritmo que resume el historial de sesion cuando excede limites de atencion (U-shaped attention). | 
 | BL-099 | Convertir documentacion MD a componentes reactivos/offline | CORE VITALS | Delegado | Content | Utilizar la Skill de UX para transformar archivos MD planos en interfaces reactivas/potentes usando frameworks ligeros opensource, mejorando la legibilidad y utilidad offline. | 
 | BL-100 | Implementar script de Aprendizaje Continuo (Optimizacion) | CORE VITALS | Hecho | Development | Automatizar la generacion de reportes de optimizacion (tokens, quota, API calls) al cierre de sesion, como se define en el AGENT.md de session-manager. | 
 | BL-101 | Onboarding Process Interactivo | CORE VITALS | Hecho | Personal | Implementar proceso de onboarding con apoyo interactivo para guiar al usuario sobre el framework, caracteristicas y uso. | 
 | BL-102 | Core Skill: ETL (Extract Transform Load) | CORE VITALS | Hecho | Development | Implementar skill para manipulacion de datos (Excel, formatos, formulas) requerida comunmente por usuarios. | 
 | BL-103 | Modulo "Centralized Knowledge Base" | CORE VITALS | Delegado | Research | Modulo/banco de URLs y mejores practicas. Delegado a Codex. | 
 | BL-104 | Feature Architect: Research & Improvement Capability | Alta | Pendiente | Development | Habilidad para consultar estado/inventario de habilidades del framework, comparar vs Papers AI usando BL-106, y documentar localmente planes de mejora/optimizacion. Dependencias: BL-103, BL-106 | 
 | BL-105 | Dev/Agent Standards Integration | Alta | Pendiente | Development | Implementar Dev/Agent complementado con estandares como BMAD, OpenSpec, OhMyCode, spec-kit. | 
 | BL-106 | Codebase Centralizada (Knowledge URLs) | CORE VITALS | Hecho | Development | Modulo centralizado de URLs de conocimiento/documentacion/mejores-practicas. Incluir: Context7, NirDiamant agents, lofi.so, deepseek-ai, serena, git-mcp, langchain-ai, GreatScottyMac context-portal, marckrenn rtfmbro-mcp, agent-skills.cc, agentman.ai, clawdhub.com, Papers AI (arxiv, huggingface, scholar), recomendaciones de modelos IA (Claude Opus 4.5 para auditar, Gemini 3 para planear, GPT 5.2 Codex Max para ejecutar). | 
 | BL-107 | Integracion CORE-Agent en Consola | Alta | Pendiente | Development | Prueba de integrar/configurar CORE-Agent (sugerido @feature-architect) como Agent en consola. Priorizar estandar Opencode (.opencode/agent/ con archivos .md para personas AI) y evaluar soporte en otras CLIs. | 
 | BL-108 | Gestion de Quotas y Alertas de Uso | Alta | Hecho | Development | Sistema para monitorear quotas de Gemini, OpenAI (GPT-5.2), x.ai y Claude. Respetar limites y avisar al usuario antes de superarlos (ref: developers.google, help.openai, docs.x.ai, support.claude). | 
 | BL-109 | Investigacion de Agent Skills & Serena | Alta | Pendiente | Development | Analizar `muratcankoylan/Agent-Skills-for-Context-Engineering` y `oraios/serena` vs Framework actual. Evaluar practicas, estandares y codigo para integracion/mejora respetando filosofia local-first. | 
 | BL-110 | Integracion DeepSeek-OCR y KeyForge | Alta | Pendiente | Development | Evaluar e implementar `deepseek-ai/DeepSeek-OCR` y `infodungeon/keyforge` como Core Skills para potenciar la lectura de documentos y generacion de claves. | 
 | BL-111 | Estandarizacion de PR para Feature Requests | CORE VITALS | Hecho | Development | Definido estandar de PR (+10% prioridad) en docs/workflow/contribution.mdx para features solicitados via Framework o GitHub. | 
 | BL-112 | Estrategia Dual-Remote (Publico/Privado) y Privacidad de Logs | CORE VITALS | Hecho | Development | Implementada estrategia Dual-Remote en setup_repo.py y .gitignore estricto para proteger logs/sessions. pa.bat soporta configuracion hibrida. | 
 | BL-113 | Soporte de Trabajo Paralelo (Multi-User Sync) | CORE VITALS | Hecho | Development | Deteccion de colisiones Git implementada en sync-context.py | 
 | BL-114 | Comando de Sincronizacion de Workspace Local | Alta | Pendiente | Development | Integrar en `pa.bat` opcion para sincronizar cambios locales de workspaces con el repo privado sin afectar el core publico. | 
 | BL-115 | Integrar Dashboard de Estadisticas Historicas (ETL + UI) | Alta | Hecho | Development | Script ETL para generar JSON historico y mejora en dashboard.html para visualizar graficos de uso y ahorro. | 
 | BL-116 | Integrar Excalidraw CLI (@excalidraw) | Media | Pendiente | Development | Wrapper para https://github.com/swiftlysingh/excalidraw-cli permitiendo diagramacion via CLI. | 
 | BL-117 | Suite de Pruebas de Integridad Ligera | Alta | Hecho | Development | Tests unitarios con `unittest` (sin deps) para validar integridad de scripts criticos y contexto. | 
 | BL-118 | En el backlog se debería poder asignar tareas a los workspaces | Media | Hecho | Development | Ahora el Backlog es nuestro registro de desarrollo, pero para el usuario será su organización CENTRAL de gestión de actividades | 
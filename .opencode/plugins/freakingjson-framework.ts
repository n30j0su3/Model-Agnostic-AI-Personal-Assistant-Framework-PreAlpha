/**
 * FreakingJSON Framework — capa de integración con OpenCode.
 *
 * Objetivo: que las skills y el comportamiento queden CONDICIONADOS al
 * framework, no a los defaults genéricos de OpenCode.
 *
 *  1. `config`  → registra las skills nativas del framework
 *                 (todas las SKILL.md bajo `core/skills/core`) de forma idempotente.
 *  2. `system`  → inyecta las reglas operativas del framework (MVI,
 *                 privacidad, persistencia, routing de workspaces).
 *
 * La ruta también se declara en `opencode.jsonc` (`skills.paths`) para que
 * resuelva incluso si el hook no estuviera disponible. Este plugin es la
 * capa auto-reparable y con alcance de framework.
 */
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync } from "node:fs"
import { join, resolve } from "node:path"

const MARKER = "<!-- freakingjson-framework -->"

const FRAMEWORK_RULES = `${MARKER}
[FreakingJSON Framework]
Operas dentro del framework personal de FreakingJSON (privacy-first, contexto local).
- Skills nativas: \`core/skills/core/<name>/SKILL.md\`. Cárgalas con la tool \`skill\` cuando apliquen; consulta \`core/skills/SKILLS.md\` antes de crear scripts (DRY).
- Gate tarea→skill: antes de crear o modificar cualquier archivo, mapea la tarea contra \`core/skills/SKILLS.md\` y la tool \`skill\`. Si una skill aplica, cárgala y úsala; si no, dilo explícitamente antes de escribir.
- Idioma: es. Estilo: MVI (conciso; 1-3 frases por concepto).
- Persistencia obligatoria: decisiones → \`core/.context/sessions/YYYY-MM-DD.md\`; ideas → \`core/.context/codebase/ideas.md\`; pendientes → \`core/.context/codebase/recordatorios.md\`; preferencias → \`core/.context/MASTER.md\`.
- Entregables → \`workspaces/<workspace>/projects/<proyecto>/\` según \`data/user/workspaces.json\`.
- Privacidad: nunca expongas credenciales; todo el conocimiento vive en disco local.`

export default (async ({ directory }) => {
  const pluginDir = (import.meta as any).dir as string | undefined
  const root = pluginDir ? resolve(pluginDir, "..", "..") : resolve(directory)
  const skillsPath = join(root, "core", "skills", "core")

  return {
    config: async (cfg) => {
      if (!existsSync(skillsPath)) return
      const config = cfg as any
      config.skills ??= {}
      config.skills.paths ??= []
      if (!config.skills.paths.includes(skillsPath)) {
        config.skills.paths.push(skillsPath)
      }
    },
    "experimental.chat.system.transform": async (_input, output) => {
      if (!Array.isArray(output.system)) return
      const already = output.system.some(
        (entry) => typeof entry === "string" && entry.includes(MARKER),
      )
      if (!already) output.system.push(FRAMEWORK_RULES)
    },
  }
}) satisfies Plugin

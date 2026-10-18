# .opencode — OpenCode Agent Configuration

## Archivos que sÍ se copian

| Archivo/Dir | Descripción |
|-------------|-------------|
| `config.json` | Configuración del agente |
| `agent/*.md` | Definiciones de agentes (FreakingJSON, pa-assistant) |
| `commands/*.md` | Comandos personalizados del framework |
| `package.json` | Dependencias npm |

## node_modules

⚠️ `node_modules/` fue movido a `_node_modules_backup/` para reducir el tamaño del proyecto.

## En una instalación nueva (Windows, Linux, Mac)

```bash
cd .opencode
npm install
```

Esto reinstalla las dependencias desde `package.json`.

## Dependencias

- `@opencode-ai/plugin`: `^1.18.18` (mínimo del runtime: `1.18.0`).

## Runtime-managed

`package.json` y `package-lock.json` son **runtime-managed**: el CLI de OpenCode
los reescribe a su propia versión. Se incluyen en el ZIP para el bootstrap,
pero **no** se certifican por hash en `MANIFEST.sha256.json`; el contrato es
semver `>= 1.18.0` y se valida en el build y en el arranque.

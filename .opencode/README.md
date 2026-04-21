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

- `@opencode-ai/plugin`: ^1.2.24

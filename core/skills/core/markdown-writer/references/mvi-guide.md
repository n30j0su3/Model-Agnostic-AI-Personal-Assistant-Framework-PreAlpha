# Guía del Principio MVI (Minimal Viable Information)

El principio MVI es fundamental para mantener la documentación del framework útil, mantenible y eficiente.

## ¿Qué es MVI?

**M**inimal **V**iable **I**nformation = Información Viable Mínima

Es el principio de documentar solo lo esencial necesario para que el lector (humano o AI) entienda y actúe, sin sobrecarga de información.

## Las 4 Reglas de MVI

### 1. Máximo 1-3 Oraciones por Concepto

**¿Por qué?**
- La atención es limitada
- Forza claridad mental
- Reduce ambigüedad

**Ejemplo:**

❌ **Sin MVI**:
```markdown
La función de autenticación es muy importante porque permite a los usuarios 
ingresar al sistema de manera segura. Esta función verifica las credenciales 
proporcionadas por el usuario contra nuestra base de datos de usuarios. 
Cuando las credenciales son correctas, se genera un token JWT que se usa 
para mantener la sesión activa durante un período de tiempo determinado.
```

✅ **Con MVI**:
```markdown
Autentica usuarios verificando credenciales contra la base de datos.
Genera token JWT con validez de 24h tras autenticación exitosa.
```

### 2. Máximo 3-5 Bullets por Sección

**¿Por qué?**
- Lists largas no se retienen
- Fuerza priorización
- Facilita scanning

**Ejemplo:**

❌ **Sin MVI**:
```markdown
## Beneficios

- Mejora la productividad
- Reduce errores
- Ahorra tiempo
- Facilita colaboración
- Mejora calidad del código
- Reduce deuda técnica
- Aumenta satisfacción del equipo
- Mejora onboarding
- Facilita mantenimiento
```

✅ **Con MVI**:
```markdown
## Beneficios Principales

- **Productividad**: Reduce tiempo en tareas repetitivas
- **Calidad**: Menos errores mediante automatización
- **Colaboración**: Estándares consistentes para todo el equipo

Ver `references/beneficios-detallados.md` para lista completa.
```

### 3. Ejemplo Mínimo cuando Aplique

**¿Por qué?**
- Un ejemplo vale más que mil palabras
- Demuestra uso práctico
- Reduce ambigüedad

**Ejemplo:**

❌ **Sin MVI**:
```markdown
Para usar la función de formateo de fechas, primero necesitas importar el 
módulo correspondiente. Luego puedes llamar a la función pasando los 
parámetros adecuados. La función acepta varios formatos de entrada y 
produce diferentes formatos de salida según tus necesidades.
```

✅ **Con MVI**:
```markdown
Formatea fechas ISO a formato legible:

```python
from utils import format_date
format_date("2026-02-11", format="long")  # "11 de febrero de 2026"
```

Ver `references/formatos.md` para opciones completas.
```

### 4. Referencia a Documentación Completa

**¿Por qué?**
- Evita duplicación
- Mantiene sincronización
- Permite profundización bajo demanda

**Ejemplo:**

❌ **Sin MVI**:
```markdown
## Configuración de Base de Datos

La configuración de la base de datos requiere especificar el host, puerto, 
nombre de la base de datos, usuario y contraseña. El host puede ser una 
dirección IP o nombre de dominio. El puerto por defecto es 5432 para 
PostgreSQL. El nombre de la base de datos debe existir previamente. 
El usuario debe tener permisos adecuados...
[50 líneas más]
```

✅ **Con MVI**:
```markdown
## Configuración

Configura conexión vía variables de entorno:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

Ver `references/database-config.md` para opciones avanzadas y troubleshooting.
```

## Aplicación por Tipo de Documento

### Sesiones Diarias

```markdown
## Tareas Completadas

- [x] Implementar endpoint de login
- [x] Agregar tests unitarios  
- [x] Documentar API

## Decisiones

**Decisión**: Usar JWT con expiración de 24h  
**Razón**: Balance entre seguridad y UX  
**Impacto**: Requiere refresh tokens en v2

## Próximos Pasos

1. Configurar envío de emails
2. Implementar recuperación de contraseña
3. Auditoría de seguridad
```

### Skills

```markdown
## Casos de Uso

1. **Extracción**: Extraer texto de PDFs escaneados
2. **Conversión**: Convertir PDFs a otros formatos
3. **Optimización**: Comprimir PDFs manteniendo calidad

## Uso

```python
from skills.pdf import extract_text
text = extract_text("documento.pdf", lang="spa")
```

Ver `references/pdf-guide.md` para opciones avanzadas.
```

### ADRs (Decisiones)

```markdown
## Alternativas Consideradas

| Opción | Pros | Contras | Decisión |
|--------|------|---------|----------|
| PostgreSQL | Robusto, escalable | Overhead de config | Rechazado |
| SQLite | Simple, portable | No concurrente | Aceptado |
| JSON files | Mínimo | Sin queries | Rechazado |

## Referencias

- [SQLite vs PostgreSQL](https://example.com)
- [Análisis completo](./analisis-completo.md)
```

## Anti-Patrones MVI

### 1. Documentación "Por si Acaso"

❌ **Mal**:
```markdown
## Historia del Proyecto

El proyecto comenzó en 2020 cuando el fundador tuvo la idea...
[3 párrafos de historia]
```

✅ **Bien**:
```markdown
## Contexto

Proyecto iniciado 2020. Migración a arquitectura actual en 2024.
Ver `references/historia.md` para detalles completos.
```

### 2. Explicaciones del Obvio

❌ **Mal**:
```markdown
## Instalación

Para instalar el software, primero debes descargarlo. Luego, ejecutas 
el instalador. Sigue las instrucciones en pantalla...
```

✅ **Bien**:
```markdown
## Instalación

```bash
curl -sSL https://install.example.com | bash
```

Ver `references/instalacion-manual.md` para opciones avanzadas.
```

### 3. Repetición de Información

❌ **Mal**:
```markdown
# En skill.md
El formato es YYYY-MM-DD según ISO 8601.

# En references/formatos.md  
El formato es YYYY-MM-DD según ISO 8601.
```

✅ **Bien**:
```markdown
# En skill.md
Usa formato ISO 8601. Ver `references/formatos.md`.

# En references/formatos.md
YYYY-MM-DD según ISO 8601 especifica...
[explicación completa con ejemplos]
```

### 4. Lists Sin Priorización

❌ **Mal**:
```markdown
## Features

- Soporte para múltiples idiomas
- Modo oscuro
- Exportación a PDF
- Integración con Slack
- Notificaciones push
- Backup automático
- API REST
- Webhooks
- Analytics
- SSO
```

✅ **Bien**:
```markdown
## Features Principales

- **Multi-idioma**: 12 idiomas soportados
- **Exportación**: PDF, Word, HTML
- **Integraciones**: Slack, Teams, Discord

## Features Adicionales

Ver `references/features-completas.md` para lista completa.
```

## Métricas de Calidad MVI

| Métrica | Objetivo | Revisar |
|---------|----------|---------|
| Palabras por sección | <150 | >200 |
| Bullets por lista | 3-5 | >7 |
| Nivel de header usado | H1-H3 | H4+ |
| Links a referencias | >0 | 0 |
| Ejemplos de código | ≥1 | 0 |

## Ejercicio Práctico

Convierte este texto a MVI:

**Original**:
```markdown
La función de logging es muy importante para cualquier aplicación porque 
permite registrar eventos y errores que ocurren durante la ejecución. 
Esto es útil para debugging y monitoreo. La función acepta diferentes 
niveles de log como DEBUG, INFO, WARNING, ERROR y CRITICAL. Cada nivel 
tiene un propósito específico. DEBUG se usa para información detallada 
durante desarrollo. INFO para eventos normales. WARNING para situaciones 
que podrían causar problemas. ERROR para errores que impiden funcionalidad. 
CRITICAL para errores graves del sistema.
```

**MVI**:
```markdown
Registra eventos con niveles de severidad:

```python
log("Usuario autenticado", level="INFO")
log("Conexión fallida", level="ERROR")
```

Niveles: DEBUG < INFO < WARNING < ERROR < CRITICAL

Ver `references/logging.md` para configuración avanzada.
```

## Recordatorio

> **MVI no es "menos documentación"**. Es **documentación enfocada**.

La meta es que cada palabra aporte valor. Si algo puede ser inferido o está en otra parte, referencia en lugar de repetir.

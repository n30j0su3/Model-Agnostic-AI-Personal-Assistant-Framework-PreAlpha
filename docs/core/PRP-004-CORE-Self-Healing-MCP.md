---
title: "CORE-004: Self-Healing + MCP"
version: "0.2.0-prealpha"
type: "process"
scope: "public"
prp: "PRP-004"
---

# CORE-004: Self-Healing + MCP

## Principio Fundamental

**Las skills deben incluir lógica de auto-recuperación (self-healing) ante errores comunes, integrando Model Context Protocol (MCP) para diagnóstico y corrección automática.**

## Descripción

El proceso CORE-004 establece que las skills del framework no solo deben detectar errores, sino también intentar auto-recuperarse aplicando recovery playbooks, integraciones MCP y lógica de fallback inteligente.

Este principio asegura:
- Menor intervención manual para errores comunes
- Recuperación automática cuando es posible
- Delegación inteligente a recursos externos (MCP)
- Fallbacks graceful degradation

## Objetivos

1. Detectar errores tempranamente
2. Aplicar auto-recuperación automáticamente
3. Integrar MCP para diagnóstico extendido
4. Documentar cuando la auto-recuperación falla

## Cuándo Aplicar

- **En desarrollo de skills**: Incluir manejo de errores con recovery
- **Errores detectados**: Intentar self-healing primero
- **Fallas complejas**: Invocar MCP servers para diagnóstico
- **Recovery exitoso**: Documentar para KB

## Flujo de Trabajo

### Paso 1: Detectar Error

La skill detecta una condición de error:
```python
try:
    # Operación que puede fallar
    result = process_data()
except KnownError as e:
    # Ir a self-healing
    self.heal_error(e)
```

### Paso 2: Intentar Auto-Recuperación

**Opción A: Recovery Playbook Interno**
```python
# Aplicar pasos del playbook
if error_type == "encoding":
    return fix_encoding()
elif error_type == "file_not_found":
    return create_default_file()
```

**Opción B: MCP Server Integration**
```python
# Consultar MCP server para diagnóstico
context7_result = query_context7(error_message)
if context7_result:
    return apply_fix(context7_result)
```

**Opción C: Fallback Graceful**
```python
# Si todo falla, fallback seguro
return default_value_or_safe_state()
```

### Paso 3: Verificar Recuperación

Validar que el fix funcionó:
- Reintentar operación original
- Verificar estado consistente
- Confirmar output correcto

### Paso 4: Documentar Resultado

**Éxito**:
- Loggear recovery exitoso
- Actualizar métricas de self-healing
- Compartir aprendizaje con KB

**Fallo**:
- Documentar en knowledge/errors/
- Escalar a error que requiere intervención
- Aplicar CORE-003 (Antifragile Error Recovery)

## Herramientas y Recursos

### Scripts
- `core/scripts/error_logger.py`: Logging de intentos de recovery
- `core/scripts/self-healing/`: Scripts de auto-recuperación

### MCP Servers
- `@context7`: Consulta documentación técnica
- `@sequentialthinking`: Análisis estructurado de problemas

### Knowledge Base
- `knowledge/self-healing/`: Logs de auto-recuperación
- `knowledge/playbooks/`: Recovery playbooks

## Ejemplos Prácticos

### Ejemplo 1: Auto-Fix Encoding

**Error**: `UnicodeEncodeError` al escribir archivo

**Self-Healing**:
1. Detectar error
2. Intentar con `encoding='utf-8'`
3. Si falla, intentar `encoding='latin-1'`
4. Verificar escritura exitosa
5. Loggear recovery

### Ejemplo 2: MCP Diagnóstico

**Error**: API desconocida devuelve error 400

**Self-Healing con MCP**:
1. Detectar error 400
2. Query a @context7: "API X error 400 common causes"
3. Aplicar fix sugerido
4. Reintentar request
5. Verificar éxito

### Ejemplo 3: Fallback Pattern

**Error**: Servicio externo no disponible

**Self-Healing**:
1. Detectar timeout
2. Reintentar con backoff (3 veces)
3. Si persiste, usar caché local
4. Si no hay caché, usar valor por defecto
5. Notificar modo degradado

## Patrones de Self-Healing

### Patrón 1: Retry con Backoff
```python
for attempt in range(max_retries):
    try:
        return operation()
    except TransientError:
        wait(backoff_time ** attempt)
return fallback()
```

### Patrón 2: Circuit Breaker
```python
if failure_count > threshold:
    return fallback_mode()
try:
    result = operation()
    reset_failure_count()
    return result
except:
    increment_failure_count()
    raise
```

### Patrón 3: MCP Consultation
```python
try:
    return operation()
except UnknownError as e:
    diagnosis = mcp_context7.diagnose(e)
    if diagnosis.has_fix():
        return apply_fix(diagnosis.fix)
    raise
```

## Integración con MCP

### MCP Servers Disponibles

| Server | Uso | Ejemplo |
|--------|-----|---------|
| @context7 | Buscar documentación | "Python encoding errors" |
| @sequentialthinking | Análisis estructurado | "Analizar causa de error" |

### Flujo MCP Integration

1. **Error detectado** → Skill intenta self-healing local
2. **Fallo local** → Consultar MCP server relevante
3. **Diagnóstico MCP** → Aplicar sugerencia
4. **Verificación** → Confirmar fix exitoso
5. **Documentación** → Actualizar KB con nuevo caso

## Validación y Verificación

- [ ] ¿La skill tiene manejo de errores robusto?
- [ ] ¿Intenta self-healing ante errores conocidos?
- [ ] ¿Integra MCP para casos complejos?
- [ ] ¿Tiene fallback graceful si todo falla?
- [ ] ¿Documenta resultados de self-healing?

## Referencias

- [AGENTS.md](../../AGENTS.md) - Router principal
- [Self-Healing](../core/.context/knowledge/self-healing/) - Logs de auto-recuperación
- [MCP Documentation](https://modelcontextprotocol.io/) - Especificación MCP

## Changelog

### v0.2.0-prealpha (2026-03-11)
- Versión inicial simplificada para release público
- Sanitizado: eliminados datos de desarrollo interno
- Agregado: patrones de self-healing comunes
- Agregado: integración con MCP servers

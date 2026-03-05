# Filosofía del Framework FreakingJSON

> "El conocimiento verdadero trasciende a lo público, pero debe permanecer bajo tu control."

---

## Principios Fundamentales

### 1. Local-First (Local Primero)

**Todo tu conocimiento reside en archivos locales que tú controlas.**

- Sin dependencia de servidores externos para funcionar
- Tus datos nunca se venden ni se usan para entrenar modelos ajenos
- Funciona offline cuando sea posible
- Tú decides qué compartir y cuándo

---

### 2. User Sovereignty (Soberanía del Usuario)

**El usuario SIEMPRE tiene el control. El framework NUNCA decide por ti. TÚ eliges cómo proceder.**

Este principio se aplica en:

- **Actualizaciones**: Cuando falla una descarga SSL, el framework presenta opciones y tú eliges:
  - Opción 1: Continuar sin verificación SSL (modo compatibilidad)
  - Opción 2: Instalar certificados SSL (solución permanente)
  - Opción 3: Descargar manualmente (control total)
  - Opción C: Cancelar y salir (sin presión)

- **Decisiones importantes**: Nunca se asume una respuesta por defecto sin consultar
- **Configuración**: Tú decides qué agente usar, qué CLI preferir, qué datos compartir

> "Tu contexto, tus reglas. Yo solo sugiero, tú decides."

---

### 3. Vendor-Agnostic (Independencia de Proveedor)

**Funciona con cualquier proveedor de IA o modelo local.**

- OpenAI, Claude, Gemini, Codex, Ollama, LM Studio...
- Sin vendor lock-in: puedes cambiar de proveedor sin perder tu conocimiento
- El framework adapta su comportamiento según el CLI detectado
- Portabilidad total entre entornos

---

### 4. Minimal Viable Information (MVI)

**Solo la información esencial, referencia el resto.**

- Documentación concisa: máximo 1-3 oraciones por concepto
- 3-5 bullets por sección
- Ejemplos mínimos cuando apliquen
- Enlaces a documentación completa en lugar de duplicar contenido

---

### 5. Transparency & Trust (Transparencia y Confianza)

**El framework explica qué hace y por qué.**

- Mensajes claros sobre qué método se está usando
- Advertencias cuando se usan modos de compatibilidad
- Explicaciones de errores en lenguaje humano
- Sin procesos ocultos o mágicos

---

### 6. Graceful Degradation (Degradación Elegante)

**Funciona incluso cuando algo falla.**

- Sin dependencias obligatorias: todo es opcional con fallback
- Si `requests` no está instalado, usa `urllib`
- Si SSL falla, presenta opciones al usuario
- Si todo falla, ofrece alternativa manual
- Nunca se bloquea por falta de una librería opcional

---

### 7. Structured Workflow (Flujo de Trabajo Estructurado)

**Todo trabajo complejo sigue el Workflow Standard 7-pasos.**

- Transparencia total: el usuario aprueba antes de ejecutar
- Eficiencia máxima: uso óptimo de skills y recursos locales
- Documentación automática: cada tarea queda registrada
- Control absoluto: el usuario decide en cada paso importante

> **Ver**: [WORKFLOW-STANDARD.md](WORKFLOW-STANDARD.md) — Proceso completo de 7 pasos

---

## Frases Insignia

### Oficial

> *"El conocimiento verdadero trasciende a lo público."*
> 
> *"True knowledge transcends to the public."*

### Operativa

> *"I own my context. I am FreakingJSON."*
> 
> — *NetworkChuck (inspiración)*

> *"El usuario siempre tiene el control. El framework NUNCA decide por ti."*

---

## Aplicación Práctica

### Ejemplo: Sistema de Update

Cuando un usuario intenta actualizar y falla el SSL:

```
[INFO] No se pudo descargar con verificación SSL.
Esto es común en Windows con Python recién instalado.

El usuario SIEMPRE tiene el control.
El framework NUNCA decide por ti. TÚ eliges cómo proceder.

Opciones disponibles:
  [1] Intentar sin verificación SSL (funciona inmediatamente)
  [2] Instalar certificados SSL (solución permanente)
  [3] Descargar manualmente
  [c] Cancelar y salir

Elige una opción [1/2/3/c]: 
```

**¿Por qué?** Porque el framework respeta tu autonomía. No decide por ti cómo resolver un problema técnico.

---

## Compromisos del Framework

| Principio | Compromiso |
|-----------|------------|
| Local-First | Tus datos nunca salen de tu PC sin tu permiso explícito |
| User Sovereignty | Cada decisión importante requiere tu aprobación |
| Vendor-Agnostic | Funciona con cualquier LLM, sin preferencias de marca |
| MVI | Documentación clara, sin relleno |
| Transparency | Explicaciones claras de errores y soluciones |
| Graceful Degradation | Siempre hay un plan B (y C, y D...) |

---

## Referencias

- [README Principal](../README.md)
- [AGENTS.md - Configuración de Agentes](../AGENTS.md)
- [CHANGELOG.md](../CHANGELOG.md)

---

*Documentación basada en la filosofía FreakingJSON v1.0*

> *"True knowledge transcends to the public."*

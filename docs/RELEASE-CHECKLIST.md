# Checklist de Release - CRÍTICO

> **Este documento debe revisarse ANTES de cada release público**
> 
> *"El conocimiento que no se documenta, se repite."*

---

## ⚠️ ERRORES CRÍTICOS DOCUMENTADOS

### Error #1: README Técnico en PROD (Grave)

**Síntoma**: README.md en repo público contiene:
- Sección "Dev HQ vs Public Release"
- Versión desactualizada en badge (ej: v0.1.0-alpha en lugar de v0.1.1-prealpha)
- Información técnica de desarrollo (`.context/`, `sync-prealpha`, etc.)
- Referencias a "Dev HQ", "BASE", "entornos de desarrollo"

**Impacto**: 
- Usuarios ven documentación técnica confusa
- Se expone información interna de desarrollo
- Versión no coincide con el tag del release
- Apariencia poco profesional

**Causa Raíz**:
- Sync manual (`cp`) no aplica la conversión `README-simple.md → README.md`
- `sync-prealpha.py` tiene lógica especial para PROD pero el sync manual no la sigue
- No hay validación POST-sync que verifique el tipo de README

**Solución Inmediata**:
```bash
# En PROD, ANTES de commit:
cd Pa_Pre_alpha_Opus_4_6

# 1. Verificar si README es el técnico
grep -q "Dev HQ vs Public Release" README.md && echo "❌ ERROR: README técnico"

# 2. Si es error, corregir:
cp ../Model-Agnostic-AI-Personal-Assistant-Framework/README-simple.md README.md

# 3. Verificar versión correcta
head -1 README.md | grep "v0.X.Y-prealpha"
```

**Prevención**: 
- ✅ Validación POST-sync obligatoria (ver abajo)
- ✅ Script `sync-prealpha.py` SIEMPRE para PROD (no manual)
- ✅ Checklist firme antes de cada tag

---

### Error #2: Rutas de Scripts Incorrectas en README (Crítico)

**Síntoma**: README-simple.md (user-friendly) contiene rutas incorrectas:
- `python3 scripts/install.py` → Ruta no existe (debe ser `core/scripts/install.py`)
- `./pa.sh` o `pa.bat` → Sin especificar directorio (correcto, están en raíz)
- Referencias a scripts en rutas antiguas post-reestructuración

**Impacto**: 
- Usuarios no pueden instalar siguiendo las instrucciones
- Error frustrante: "No such file or directory"
- Abandono de instalación por usuarios nuevos
- Mala primera impresión del framework

**Causa Raíz**:
- README-simple.md no se actualizó tras reestructuración del proyecto
- Scripts movidos de `scripts/` → `core/scripts/` sin actualizar docs
- No hay validación de comandos antes de release

**Solución Inmediata**:
```bash
# En BASE, verificar ANTES de sync:
grep -n "scripts/install" README-simple.md
# Debe mostrar: core/scripts/install.py

# Verificar otras rutas comunes:
grep -E "(scripts/|core/)" README-simple.md | grep -v "core/scripts"
```

**Prevención**: 
- ✅ Agregar a checklist: "Verificar rutas de comandos en README-simple.md"
- ✅ Script de validación: `validate-readme-paths.py`
- ✅ Testing manual: Ejecutar comandos documentados antes de release

---

### Error #3: Archivo VERSION Desactualizado

**Síntoma**: `VERSION` contiene versión anterior (ej: `0.1.0-alpha`)

**Impacto**:
- Script `update.py` no detecta nuevas versiones
- Usuarios no reciben notificaciones de actualización
- Mecanismo de auto-update falla

**Causa Raíz**:
- Se olvida actualizar el archivo `VERSION` en BASE antes del sync
- No está documentado como requisito crítico

**Solución**:
```bash
# En BASE, ANTES de sync:
echo "0.1.1-prealpha" > VERSION
git add VERSION && git commit -m "chore: VERSION v0.1.1-prealpha"
```

---

### Error #4: Tag con Contenido Incorrecto

**Síntoma**: Tag apunta a commit que tiene README técnico

**Impacto**:
- Release público permanente con errores
- Difícil de corregir sin force-push (no recomendado)
- Solo solución: borrar tag y recrear (confusión)

**Solución**:
```bash
# Eliminar tag incorrecto
git tag -d v0.1.1-prealpha
git push origin :refs/tags/v0.1.1-prealpha

# Crear nuevo tag en commit corregido
git tag -a v0.1.1-prealpha -m "Release v0.1.1-prealpha"
git push origin v0.1.1-prealpha
```

---

## ✅ CHECKLIST PRE-RELEASE (OBLIGATORIO)

### FASE 1: Preparación en BASE

- [ ] **Actualizar VERSION**
  ```bash
  echo "0.X.Y-prealpha" > VERSION
  git add VERSION && git commit -m "chore: VERSION vX.Y.Z-prealpha"
  ```

- [ ] **Actualizar CHANGELOG.md**
  - Sección `[0.X.Y-prealpha] - YYYY-MM-DD`
  - Documentar todos los cambios significativos
  - Referencias a issues/PRs si aplica

- [ ] **Verificar README-simple.md**
  - Versión correcta en título y badge
  - Sin sección "Dev HQ vs Public Release"
  - Contenido user-friendly (no técnico)
  - **Rutas de comandos correctas**:
    ```bash
    # Verificar instalación Mac/Linux
    grep "python3.*install.py" README-simple.md
    # Debe mostrar: python3 core/scripts/install.py
    
    # Verificar no hay rutas antiguas
    grep -E "^python3 scripts/" README-simple.md && echo "❌ ERROR: Rutas antiguas"
    ```

- [ ] **Commit en BASE**
  ```bash
  git push origin main
  ```

### FASE 2: Sync a DEV

- [ ] **Ejecutar sync a DEV**
  ```bash
  python core/scripts/sync-prealpha.py --mode=dev
  ```

- [ ] **Validar en DEV**
  ```bash
  cd Pa_Pre_alpha_Opus_4_6_DEV
  head -1 README.md  # Verificar versión
  ```

- [ ] **Commit en DEV**
  ```bash
  git add -A && git commit -m "sync: vX.Y.Z-prealpha"
  ```

### FASE 3: Sync a PROD (CRÍTICO)

- [ ] **Ejecutar sync a PROD**
  ```bash
  python core/scripts/sync-prealpha.py --mode=prod
  ```

- [ ] **✅ VALIDACIÓN POST-SYNC (NO SALTAR)**
  ```bash
  cd Pa_Pre_alpha_Opus_4_6
  
  # Check 1: README es user-friendly
  if grep -q "Dev HQ vs Public Release" README.md; then
    echo "❌ ERROR CRÍTICO: README técnico detectado"
    echo "SOLUCIÓN: cp ../README-simple.md README.md"
    exit 1
  fi
  
  # Check 2: Versión correcta
  head -1 README.md | grep -q "v0.X.Y-prealpha" || {
    echo "❌ ERROR: Versión incorrecta en README"
    exit 1
  }
  
  # Check 3: CHANGELOG actualizado
  grep -q "\[0.X.Y-prealpha\]" CHANGELOG.md || {
    echo "❌ ERROR: CHANGELOG no actualizado"
    exit 1
  }
  
  # Check 4: VERSION actualizado
  cat VERSION | grep -q "0.X.Y-prealpha" || {
    echo "❌ ERROR: VERSION no actualizado"
    exit 1
  }
  
  echo "✅ TODAS LAS VALIDACIONES PASARON"
  ```

- [ ] **Copiar README-simple.md como README.md**
  ```bash
  # IMPORTANTE: sync-prealpha.py debería hacer esto, pero verificar
  cp ../Model-Agnostic-AI-Personal-Assistant-Framework/README-simple.md README.md
  ```

- [ ] **Commit en PROD**
  ```bash
  git add -A
  git commit -m "release: vX.Y.Z-prealpha"
  ```

### FASE 4: Tag y Publicación

- [ ] **Eliminar tag anterior si existe**
  ```bash
  git tag -d vX.Y.Z-prealpha 2>/dev/null
  git push origin :refs/tags/vX.Y.Z-prealpha 2>/dev/null
  ```

- [ ] **Crear nuevo tag**
  ```bash
  git tag -a vX.Y.Z-prealpha -m "Release vX.Y.Z-prealpha - Descripción"
  ```

- [ ] **Push a upstream**
  ```bash
  git push origin main
  git push origin vX.Y.Z-prealpha
  ```

### FASE 5: Verificación Web (5 min después)

- [ ] **Verificar README remoto**
  ```bash
  curl -s https://raw.githubusercontent.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/main/README.md | head -1
  # Debe mostrar: # Model-Agnostic AI Personal Assistant Framework vX.Y.Z-prealpha
  ```

- [ ] **Verificar sin Dev HQ**
  ```bash
  curl -s https://raw.githubusercontent.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/main/README.md | grep -q "Dev HQ" && echo "❌ ERROR" || echo "✅ OK"
  ```

- [ ] **Verificar VERSION remoto**
  ```bash
  curl -s https://raw.githubusercontent.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-PreAlpha/main/VERSION
  ```

---

## 🚨 PROTOCOLO DE EMERGENCIA

Si se descubre un error DESPUÉS del release:

### Escenario A: README incorrecto (como ahora)

1. **No entres en pánico** - Es recuperable
2. **Corregir en PROD local**
   ```bash
   cd Pa_Pre_alpha_Opus_4_6
   cp ../README-simple.md README.md
   git add README.md && git commit -m "fix: README corregido"
   ```
3. **Recrear tag**
   ```bash
   git tag -d vX.Y.Z-prealpha
   git push origin :refs/tags/vX.Y.Z-prealpha
   git tag -a vX.Y.Z-prealpha -m "Release vX.Y.Z-prealpha (fix)"
   git push origin vX.Y.Z-prealpha
   ```
4. **Verificar en 5 minutos**
   ```bash
   curl -s .../README.md | head -1
   ```

### Escenario B: Error grave que requiere nuevo release

1. Crear versión patch: `v0.1.2-prealpha`
2. Corregir problema en BASE
3. Repetir proceso completo de checklist
4. Documentar en CHANGELOG el fix

---

## 📊 Historial de Errores y Soluciones

| Fecha | Error | Solución | Prevenido por |
|-------|-------|----------|---------------|
| 2026-03-03 | README técnico en PROD | Re-tag con README-simple.md | Validación POST-sync |
| 2026-03-03 | Rutas incorrectas README | Corregir a core/scripts/install.py | Checklist verificación rutas |
| 2026-03-03 | VERSION desactualizado | Commit explícito de VERSION | Checklist FASE 1 |

---

## 🔧 Mejoras Futuras del Proceso

1. **Script de validación automática**: `validate-release.py`
   - Verifica README, VERSION, CHANGELOG antes de permitir tag
   
2. **GitHub Action**: Pre-release validation
   - Bloquea releases que no pasen validaciones
   
3. **sync-prealpha.py mejorado**
   - Automáticamente copia README-simple.md → README.md en PROD
   - Alerta si VERSION no coincide con tag

---

## Referencias

- [PHILOSOPHY.md](./PHILOSOPHY.md) - Principios del framework
- [CHANGELOG.md](../CHANGELOG.md) - Historial de cambios
- [docs/RELEASES/](./RELEASES/) - Notas de releases anteriores

---

*Documentación creada tras incidente del 2026-03-03*
*Última actualización: 2026-03-03*

> *"El conocimiento verdadero trasciende a lo público, pero los errores documentados no se repiten."*

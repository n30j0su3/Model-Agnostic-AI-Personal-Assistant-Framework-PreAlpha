# Guía Rápida - Vitals Guardian

> **Protege tus datos del framework en 3 minutos**

---

## 🚨 ¿Perdiste archivos?

### Recuperación Rápida (30 segundos)

```bash
# 1. Listar backups disponibles
python core/scripts/vitals-guardian.py list

# 2. Restaurar (selecciona el número del backup)
python core/scripts/vitals-guardian.py restore
# Ingresa: 1 (o el número del backup más reciente)

# 3. Confirmar restauración: SI
```

✅ **Listo** - Tus archivos vitales han sido recuperados.

---

## 🛡️ Protección Diaria

### Antes de operaciones riesgosas

```bash
# Crear backup manual antes de cambios importantes
python core/scripts/vitals-guardian.py snapshot --reason "antes_refactor"
```

### Ejecutar comandos destructivos de forma segura

```bash
# En lugar de: rm -rf workspaces/
# Usa:
python core/scripts/safe-executor.py -- "rm -rf workspaces/"

# El sistema detectará el riesgo y creará backup automático
```

---

## 📋 Verificación

### Al inicio de cada sesión

El sistema verifica automáticamente la integridad. Si ves:

```
[OK] Todos los archivos vitales estan intactos
```

✅ Todo está bien.

Si ves:

```
[!] ARCHIVOS CRITICOS FALTANTES (X):
   [X] workspaces/importante.txt
```

👉 **Ejecuta inmediatamente:**
```bash
python core/scripts/vitals-guardian.py restore
```

---

## 🔄 Sincronización Remota

### Backup en la nube (automático)

```bash
# Sync manual cuando quieras
python core/scripts/vitals-guardian.py sync

# O usa git directamente:
git push vitals-backup main
```

### Configurar por primera vez

```bash
python core/scripts/vitals-remote-setup.py --auto
```

---

## 📁 ¿Qué se protege?

- ✅ `workspaces/` - Tu trabajo personal
- ✅ `core/.context/sessions/` - Sesiones diarias
- ✅ `core/.context/codebase/` - Backlog, ideas, recordatorios
- ✅ `core/.context/dev-todo/` - Pendientes de desarrollo
- ✅ `config/` - Configuraciones
- ✅ `core/agents/` - Agentes personalizados
- ✅ `core/skills/custom/` - Skills personalizadas
- ✅ `**/OBSOLETE*/` - Histórico obsoleto

**Total:** ~1600 archivos protegidos automáticamente

---

## ❓ FAQ

**¿Puedo desactivar la protección?**
No recomendado. Pero puedes editar `core/.context/vitals/vitals.config.json`

**¿Cuánto espacio ocupan los backups?**
~10-15 MB por backup. Se mantienen máximo 50 backups (últimos 30 días).

**¿Los backups incluyen credenciales?**
No. Los archivos `.env`, `*.key`, `*.secret` están excluidos automáticamente.

**¿Qué pasa si borro un backup accidentalmente?**
Los backups se sincronizan con el repo remoto `vitals-backup`. Puedes recuperarlos desde ahí.

**¿Puedo restaurar solo un archivo específico?**
Sí. Los backups están en `core/.context/vitals/backups/YYYY-MM-DD_HH-MM-SS_razon/`. Copia manualmente el archivo que necesites.

---

## 🆘 Emergencias

### Disco duro falla / Repo corrupto

1. Clonar repo desde GitHub:
```bash
git clone https://github.com/n30j0su3/Model-Agnostic-AI-Personal-Assistant-Framework-dev.git
```

2. Copiar backups al nuevo framework:
```bash
cp -r Model-Agnostic-AI-Personal-Assistant-Framework-dev/vitals/* \
     /nuevo/framework/core/.context/vitals/
```

3. Restaurar:
```bash
cd /nuevo/framework
python core/scripts/vitals-guardian.py restore
```

---

## 📖 Más información

- Documentación completa: `docs/VITALS-GUARDIAN.md`
- Configuración: `core/.context/vitals/vitals.config.json`
- Logs: `core/.context/vitals/vitals.log`

---

> **Recuerda:** *El conocimiento que no se guarda, se pierde.* 
> 
> Vitals Guardian garantiza que esto NUNCA te pase. 🛡️
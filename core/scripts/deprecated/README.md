# Scripts deprecados

No soportados en v0.4.1-beta. Solo se conserva código no destructivo necesario para trazabilidad.

- `dashboard_launcher.py` — launcher del dashboard; falla en Windows reportado.
  Reemplazo: `pa.bat` (menú) o `python core/scripts/dashboard_server.py` (puente del dashboard).
- El desinstalador deprecado fue retirado: podía borrar dependencias globales fuera de `REPO_ROOT`.

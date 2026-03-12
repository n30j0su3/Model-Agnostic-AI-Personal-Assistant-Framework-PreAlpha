#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi-cli-coordinator.py - Coordinador principal para Multi-CLI
Para FreakingJSON-PA Framework

Gestiona:
- Registro de instancias CLI con heartbeat
- Sincronización en tiempo real entre CLIs
- Locks distribuidos para archivos compartidos
- Detección y manejo de conflictos
- Merge automático de sesiones

Uso:
    from multi_cli_coordinator import MultiCLICoordinator

    coord = MultiCLICoordinator(model="GPT-4")
    coord.start()  # Registra instancia e inicia servicios

    # Editar archivo con protección
    with coord.lock_file("recordatorios.md"):
        # editar archivo
        pass

    coord.shutdown()  # Limpieza al salir

Autor: FreakingJSON-PA Framework
Versión: 1.0.0
"""

import os
import sys

# Configurar UTF-8 para Windows (solo si es un terminal interactivo)
if sys.platform == "win32" and sys.stdout.isatty():
    try:
        import io

        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except (ValueError, AttributeError):
        pass
import json
import time
import atexit
import signal
import shutil
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Importar módulos del framework
sys.path.insert(0, str(Path(__file__).parent))
from file_lock import FileLock, lock_resource, LockTimeoutError
from event_bridge import EventBridge, EventType, Event


def safe_print(message: str, file=None):
    """Imprime un mensaje manejando errores de encoding."""
    output = file if file else sys.stdout
    try:
        output.write(message + "\n")
    except UnicodeEncodeError:
        # Fallback a ASCII con reemplazo de caracteres no soportados
        safe_msg = message.encode("ascii", "replace").decode("ascii")
        output.write(safe_msg + "\n")
    except Exception:
        pass  # Silenciar errores de I/O


@dataclass
class InstanceInfo:
    """Información de una instancia CLI"""

    instance_id: str
    pid: int
    model: str
    start_time: str
    last_heartbeat: str
    status: str  # active, disconnected, stale
    open_files: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstanceInfo":
        return cls(**data)


class MultiCLICoordinator:
    """
    Coordinador central para múltiples instancias CLI.

    Responsabilidades:
    1. Registro de instancias con heartbeat
    2. Comunicación entre CLIs vía eventos
    3. Gestión de locks distribuidos
    4. Detección de conflictos
    5. Cleanup de instancias muertas
    """

    HEARTBEAT_INTERVAL = 30.0  # segundos
    STALE_THRESHOLD = 120.0  # 2 minutos sin heartbeat = stale
    CLEANUP_INTERVAL = 60.0  # Cleanup cada minuto

    def __init__(
        self,
        model: str = "unknown",
        session_date: Optional[str] = None,
        instance_id: Optional[str] = None,
    ):
        """
        Args:
            model: Nombre del modelo/CLI (GPT-4, Claude, etc.)
            session_date: Fecha de sesión (default: hoy)
            instance_id: ID específico (auto-generado si no se provee)
        """
        self.model = model
        self.session_date = session_date or datetime.now().strftime("%Y-%m-%d")
        self.instance_id = instance_id or self._generate_instance_id()
        self.pid = os.getpid()
        self.start_time = datetime.now()

        # Directorios
        self.sessions_dir = Path("core/.context/sessions")
        self.instances_dir = self.sessions_dir / ".instances"
        self.sync_dir = self.sessions_dir / ".sync"
        self.conflicts_dir = self.sessions_dir / ".conflicts"

        for d in [self.instances_dir, self.sync_dir, self.conflicts_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Event bridge
        self.event_bridge: Optional[EventBridge] = None

        # Locks activos
        self._active_locks: Dict[str, FileLock] = {}
        self._locks_lock = threading.Lock()

        # Threads
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False

        # Callbacks de notificación
        self._notification_callbacks: List[Callable[[str, str], None]] = []

        # Registro de archivos modificados por esta instancia
        self._modified_files: Set[str] = set()

        # Setup cleanup
        atexit.register(self.shutdown)

        # Manejar señales
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._signal_handler)
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, self._signal_handler)

    def _generate_instance_id(self) -> str:
        """Genera ID único para esta instancia"""
        import uuid

        return f"cli-{uuid.uuid4().hex[:8]}"

    def _signal_handler(self, signum, frame):
        """Maneja señales de terminación"""
        self.shutdown()
        sys.exit(0)

    def start(self) -> bool:
        """
        Inicia el coordinador y registra la instancia.

        Returns:
            True si se inició correctamente
        """
        if self._running:
            return True

        # Crear archivo de instancia
        self._register_instance()

        # Iniciar event bridge
        self.event_bridge = EventBridge(self.instance_id, self.session_date)

        # Suscribirse a eventos relevantes
        self._setup_event_handlers()

        self.event_bridge.start_listening()

        # Iniciar threads
        self._running = True

        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name=f"Heartbeat-{self.instance_id}",
        )
        self._heartbeat_thread.start()

        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop, daemon=True, name=f"Cleanup-{self.instance_id}"
        )
        self._cleanup_thread.start()

        # Notificar unión
        self._notify_user(
            "multi-cli", f"[START] Instancia {self.instance_id} ({self.model}) iniciada"
        )

        # Verificar otras instancias activas
        other_instances = self.get_other_active_instances()
        if other_instances:
            for inst in other_instances:
                self._notify_user(
                    "multi-cli",
                    f"[ACTIVE] CLI activa detectada: {inst['instance_id']} ({inst.get('model', 'unknown')})",
                )

        return True

    def shutdown(self):
        """Detiene el coordinador y limpia recursos"""
        if not self._running:
            return

        self._running = False

        # Liberar todos los locks
        with self._locks_lock:
            for resource, lock in list(self._active_locks.items()):
                lock.release()
                self._notify_user(
                    "multi-cli", f"[UNLOCK] Lock liberado automáticamente: {resource}"
                )

        # Detener event bridge
        if self.event_bridge:
            self.event_bridge.stop_listening()

        # Eliminar archivo de instancia
        self._unregister_instance()

        # Esperar threads
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2.0)

        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2.0)

        self._notify_user("multi-cli", f"[BYE] Instancia {self.instance_id} desconectada")

    def _register_instance(self):
        """Crea el archivo de registro de instancia"""
        instance_info = InstanceInfo(
            instance_id=self.instance_id,
            pid=self.pid,
            model=self.model,
            start_time=self.start_time.isoformat(),
            last_heartbeat=datetime.now().isoformat(),
            status="active",
            open_files=[],
        )

        instance_file = self.instances_dir / f"{self.instance_id}.json"
        with open(instance_file, "w") as f:
            json.dump(instance_info.to_dict(), f, indent=2)

    def _unregister_instance(self):
        """Elimina el archivo de registro de instancia"""
        instance_file = self.instances_dir / f"{self.instance_id}.json"
        try:
            if instance_file.exists():
                instance_file.unlink()
        except OSError:
            pass

    def _update_instance_info(self, **kwargs):
        """Actualiza información de la instancia"""
        instance_file = self.instances_dir / f"{self.instance_id}.json"

        try:
            if instance_file.exists():
                with open(instance_file, "r") as f:
                    data = json.load(f)

                data.update(kwargs)
                data["last_heartbeat"] = datetime.now().isoformat()

                with open(instance_file, "w") as f:
                    json.dump(data, f, indent=2)
        except (OSError, json.JSONDecodeError):
            pass

    def _heartbeat_loop(self):
        """Loop de heartbeat periódico"""
        while self._running:
            try:
                # Actualizar archivo de instancia
                self._update_instance_info()

                # Enviar evento de heartbeat
                if self.event_bridge:
                    self.event_bridge.send_heartbeat(self.model)

                time.sleep(self.HEARTBEAT_INTERVAL)

            except Exception as e:
                print(f"[Coordinator] Error en heartbeat: {e}")
                time.sleep(self.HEARTBEAT_INTERVAL)

    def _cleanup_loop(self):
        """Loop de limpieza de instancias muertas"""
        while self._running:
            try:
                self._cleanup_stale_instances()
                time.sleep(self.CLEANUP_INTERVAL)
            except Exception as e:
                print(f"[Coordinator] Error en cleanup: {e}")
                time.sleep(self.CLEANUP_INTERVAL)

    def _cleanup_stale_instances(self):
        """Elimina instancias que no han enviado heartbeat"""
        now = datetime.now()

        try:
            for instance_file in self.instances_dir.glob("cli-*.json"):
                try:
                    with open(instance_file, "r") as f:
                        data = json.load(f)

                    instance_id = data.get("instance_id")

                    # No limpiarnos a nosotros mismos
                    if instance_id == self.instance_id:
                        continue

                    last_heartbeat = datetime.fromisoformat(
                        data.get("last_heartbeat", "2000-01-01")
                    )

                    if (now - last_heartbeat).total_seconds() > self.STALE_THRESHOLD:
                        # Verificar si el proceso existe
                        pid = data.get("pid")
                        if pid and not self._is_process_alive(pid):
                            # Proceso muerto, limpiar
                            instance_file.unlink()
                            self._notify_user(
                                "multi-cli",
                                f"[CLEANUP] Instancia muerta limpiada: {instance_id}",
                            )

                except (OSError, json.JSONDecodeError, ValueError):
                    # Archivo corrupto, eliminar
                    try:
                        instance_file.unlink()
                    except OSError:
                        pass

        except Exception as e:
            print(f"[Coordinator] Error limpiando instancias: {e}")

    def _is_process_alive(self, pid: int) -> bool:
        """Verifica si un proceso existe"""
        if os.name == "nt":  # Windows
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, False, pid)
                if handle == 0:
                    return False
                kernel32.CloseHandle(handle)
                return True
            except Exception:
                return False
        else:  # Unix
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False

    def _setup_event_handlers(self):
        """Configura handlers de eventos"""
        if not self.event_bridge:
            return

        # Instancia se unió
        self.event_bridge.subscribe(EventType.INSTANCE_JOINED, self._on_instance_joined)

        # Instancia se fue
        self.event_bridge.subscribe(EventType.INSTANCE_LEFT, self._on_instance_left)

        # Archivo modificado
        self.event_bridge.subscribe(EventType.FILE_MODIFIED, self._on_file_modified)

        # Archivo lockeado/deslockeado
        self.event_bridge.subscribe(EventType.FILE_LOCKED, self._on_file_locked)
        self.event_bridge.subscribe(EventType.FILE_UNLOCKED, self._on_file_unlocked)

        # Conflicto
        self.event_bridge.subscribe(EventType.FILE_CONFLICT, self._on_conflict)

        # Notificaciones de usuario
        self.event_bridge.subscribe(
            EventType.USER_NOTIFICATION, self._on_user_notification
        )

    def _on_instance_joined(self, event: Event):
        """Handler: nueva instancia se unió"""
        if event.source != self.instance_id:
            instance_id = event.data.get("instance_id", "unknown")
            model = event.data.get("model", "unknown")
            self._notify_user(
                "multi-cli", f"[ACTIVE] Nueva CLI conectada: {instance_id} ({model})"
            )

    def _on_instance_left(self, event: Event):
        """Handler: instancia se desconectó"""
        if event.source != self.instance_id:
            instance_id = event.data.get("instance_id", "unknown")
            self._notify_user("multi-cli", f"[BYE] CLI desconectada: {instance_id}")

    def _on_file_modified(self, event: Event):
        """Handler: archivo modificado por otra instancia"""
        if event.source != self.instance_id:
            file_path = event.data.get("file", "unknown")
            change = event.data.get("change", "")

            # Solo notificar si no fue modificado por nosotros
            if file_path not in self._modified_files:
                msg = f"[FILE] [Sync] {file_path} actualizado por {event.source}"
                if change:
                    msg += f" ({change})"
                self._notify_user("sync", msg)

    def _on_file_locked(self, event: Event):
        """Handler: archivo lockeado"""
        if event.source != self.instance_id:
            file_path = event.data.get("file", "unknown")
            self._notify_user("sync", f"[LOCK] {file_path} lockeado por {event.source}")

    def _on_file_unlocked(self, event: Event):
        """Handler: archivo deslockeado"""
        if event.source != self.instance_id:
            file_path = event.data.get("file", "unknown")
            self._notify_user("sync", f"[UNLOCK] {file_path} liberado por {event.source}")

    def _on_conflict(self, event: Event):
        """Handler: conflicto detectado"""
        file_path = event.data.get("file", "unknown")
        instances = event.data.get("instances", [])
        self._notify_user(
            "conflict",
            f"[WARN] CONFLICTO en {file_path}. Instancias: {', '.join(instances)}",
        )

    def _on_user_notification(self, event: Event):
        """Handler: notificación de usuario"""
        level = event.data.get("level", "info")
        message = event.data.get("message", "")
        self._notify_user(level, message)

    def _notify_user(self, level: str, message: str):
        """Notifica al usuario vía callbacks y/o stdout"""
        # Llamar callbacks registrados
        for callback in self._notification_callbacks:
            try:
                callback(level, message)
            except Exception:
                pass

        # También imprimir
        prefix = {
            "multi-cli": "[Multi-CLI]",
            "sync": "[Sync]",
            "conflict": "[Conflict]",
            "info": "[Info]",
            "warning": "[Warning]",
            "error": "[Error]",
        }.get(level, "[Multi-CLI]")

        print(f"{prefix} {message}")

    def register_notification_callback(self, callback: Callable[[str, str], None]):
        """Registra un callback para notificaciones"""
        self._notification_callbacks.append(callback)

    def get_active_instances(self) -> List[Dict[str, Any]]:
        """Obtiene todas las instancias activas"""
        instances = []
        now = datetime.now()

        try:
            for instance_file in self.instances_dir.glob("cli-*.json"):
                try:
                    with open(instance_file, "r") as f:
                        data = json.load(f)

                    last_heartbeat = datetime.fromisoformat(
                        data.get("last_heartbeat", "2000-01-01")
                    )

                    # Solo incluir si heartbeat reciente
                    if (now - last_heartbeat).total_seconds() <= self.STALE_THRESHOLD:
                        instances.append(data)

                except (OSError, json.JSONDecodeError, ValueError):
                    continue

        except Exception as e:
            print(f"[Coordinator] Error leyendo instancias: {e}")

        return instances

    def get_other_active_instances(self) -> List[Dict[str, Any]]:
        """Obtiene instancias activas excepto la nuestra"""
        return [
            i
            for i in self.get_active_instances()
            if i.get("instance_id") != self.instance_id
        ]

    @contextmanager
    def lock_file(self, file_path: str, timeout: float = 300.0):
        """
        Context manager para lockear un archivo.

        Args:
            file_path: Ruta del archivo a lockear
            timeout: Timeout en segundos

        Yields:
            FileLock instance

        Raises:
            LockTimeoutError: Si no se puede adquirir el lock
        """
        lock = FileLock(file_path, self.instance_id)

        # Notificar que vamos a lockear
        if self.event_bridge:
            self.event_bridge.publish(
                EventType.FILE_LOCKED,
                {
                    "file": file_path,
                    "instance_id": self.instance_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        try:
            if not lock.acquire(timeout=timeout):
                owner = lock.get_owner()
                owner_info = f" (owned by {owner.instance_id})" if owner else ""
                raise LockTimeoutError(
                    f"No se pudo adquirir lock para {file_path}{owner_info}. "
                    f"Otra CLI está editando este archivo."
                )

            # Registrar lock activo
            with self._locks_lock:
                self._active_locks[file_path] = lock

            yield lock

        finally:
            # Liberar lock
            lock.release()

            with self._locks_lock:
                if file_path in self._active_locks:
                    del self._active_locks[file_path]

            # Notificar liberación
            if self.event_bridge:
                self.event_bridge.publish(
                    EventType.FILE_UNLOCKED,
                    {
                        "file": file_path,
                        "instance_id": self.instance_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

    def notify_file_change(self, file_path: str, change_description: str = ""):
        """
        Notifica que se modificó un archivo.

        Args:
            file_path: Ruta del archivo modificado
            change_description: Descripción del cambio
        """
        self._modified_files.add(file_path)

        if self.event_bridge:
            self.event_bridge.publish(
                EventType.FILE_MODIFIED,
                {
                    "file": file_path,
                    "change": change_description,
                    "instance_id": self.instance_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    def get_session_file_with_merge(self) -> Path:
        """
        Obtiene el archivo de sesión, mergeando cambios de otras CLIs si es necesario.

        Returns:
            Path al archivo de sesión
        """
        session_file = self.sessions_dir / f"{self.session_date}.md"

        # Verificar si hay cambios de otras instancias que necesitemos mergear
        other_instances = self.get_other_active_instances()

        if len(other_instances) > 0:
            # Hay otras instancias activas
            # El archivo de sesión es compartido, se mergea automáticamente
            # por el sistema de append en secciones
            pass

        return session_file

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()
        return False


# Funciones de conveniencia


def get_coordinator(
    model: str = "unknown", session_date: Optional[str] = None
) -> MultiCLICoordinator:
    """
    Factory para obtener un coordinador inicializado.

    Uso:
        coord = get_coordinator("GPT-4")
        coord.start()
        # ... usar ...
        coord.shutdown()
    """
    return MultiCLICoordinator(model, session_date)


# CLI para testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multi-CLI Coordinator")
    parser.add_argument("--model", "-m", default="test", help="Nombre del modelo/CLI")
    parser.add_argument("--instance-id", "-i", help="ID de instancia específico")
    parser.add_argument(
        "--action",
        "-a",
        choices=["start", "status", "test-lock", "cleanup"],
        default="start",
    )

    args = parser.parse_args()

    if args.action == "start":
        print(f"[LAUNCH] Iniciando coordinador como {args.model}...")
        coord = MultiCLICoordinator(args.model, instance_id=args.instance_id)

        try:
            coord.start()
            print("Presiona Ctrl+C para salir\n")

            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n[BYE] Cerrando...")
            coord.shutdown()

    elif args.action == "status":
        coord = MultiCLICoordinator(args.model)
        instances = coord.get_active_instances()

        print(f"[INSTANCES] Instancias activas: {len(instances)}")
        for inst in instances:
            print(f"  - {inst['instance_id']} ({inst['model']})")
            print(f"    PID: {inst['pid']}, Status: {inst['status']}")
            print(f"    Desde: {inst['start_time']}")
            print(f"    Último heartbeat: {inst['last_heartbeat']}")
            print()

    elif args.action == "test-lock":
        test_file = "test-file.txt"
        coord = MultiCLICoordinator(args.model)
        coord.start()

        print(f"[LOCK] Intentando lockear {test_file}...")
        try:
            with coord.lock_file(test_file, timeout=5.0):
                print(f"[OK] Lock adquirido. Manteniendo por 10 segundos...")
                time.sleep(10)
            print("[UNLOCK] Lock liberado")
        except LockTimeoutError as e:
            print(f"[FAIL] {e}")

        coord.shutdown()

    elif args.action == "cleanup":
        print("[CLEANUP] Limpiando instancias muertas...")
        coord = MultiCLICoordinator(args.model)
        coord._cleanup_stale_instances()
        print("[OK] Cleanup completado")

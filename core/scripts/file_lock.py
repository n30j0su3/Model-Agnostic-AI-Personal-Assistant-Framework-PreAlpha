#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file-lock.py - Módulo de locking de archivos cross-platform
Para FreakingJSON-PA Multi-CLI Framework

Uso:
    from file_lock import FileLock, acquire_lock, release_lock

    # Context manager (recomendado)
    with FileLock("archivo.txt", timeout=5.0):
        # código seguro
        pass

    # Manual
    lock = FileLock("archivo.txt")
    if lock.acquire(timeout=5.0):
        try:
            # código seguro
            pass
        finally:
            lock.release()

Autor: FreakingJSON-PA Framework
Versión: 1.0.0
"""

import errno
import hashlib
import os
import sys

# Configurar UTF-8 para Windows, incluso con stdout/stderr redirigidos
if sys.platform == "win32":
    try:
        
        # v0.4.0-beta fix: reconfigure in-place (TextIOWrapper nuevo dejaba un wrapper
# huérfano que su GC cerraba → "I/O operation on closed file"/"lost sys.stderr" al salir)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass
import time
import json
import atexit
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import contextmanager
from dataclasses import dataclass, asdict

# Detección de plataforma
IS_WINDOWS = os.name == "nt"
IS_POSIX = os.name == "posix"


@dataclass
class LockInfo:
    """Información de un lock adquirido"""

    instance_id: str
    pid: int
    timestamp: str
    timeout: float
    resource: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LockInfo":
        return cls(**data)


class FileLock:
    """
    Implementación cross-platform de file locking.

    Usa archivo .lock con metadata JSON para máxima compatibilidad.
    Soporta timeout, auto-release, y detección de procesos muertos.
    """

    DEFAULT_TIMEOUT = 300.0  # 5 minutos
    DEFAULT_POLL_INTERVAL = 0.1  # 100ms
    LOCK_EXTENSION = ".lock"

    def __init__(self, resource_path: str, instance_id: Optional[str] = None):
        """
        Args:
            resource_path: Ruta al archivo a lockear
            instance_id: ID único de la instancia CLI (auto-generado si no se provee)
        """
        self.resource_path = Path(resource_path).resolve()
        self.lock_path = self._get_lock_path()
        self.instance_id = instance_id or self._generate_instance_id()
        self.pid = os.getpid()
        self._owned = False
        self._lock_info: Optional[LockInfo] = None

        # Auto-release al salir
        atexit.register(self._cleanup_at_exit)

    def _generate_instance_id(self) -> str:
        """Genera ID único para esta instancia"""
        import uuid

        return f"cli-{uuid.uuid4().hex[:8]}"

    def _get_lock_path(self) -> Path:
        """Obtiene la ruta del archivo de lock"""
        configured_dir = os.environ.get("PA_FRAMEWORK_LOCK_DIR")
        framework_root = Path(__file__).resolve().parents[2]
        base_dir = Path(configured_dir).resolve() if configured_dir else (
            framework_root / "core" / ".context" / "sessions" / ".locks"
        )
        base_dir.mkdir(parents=True, exist_ok=True)

        resource_key = os.path.normcase(str(self.resource_path))
        digest = hashlib.sha256(resource_key.encode("utf-8")).hexdigest()[:12]
        return base_dir / f"{self.resource_path.name}.{digest}{self.LOCK_EXTENSION}"

    def _read_lock(self) -> Optional[LockInfo]:
        """Read lock metadata without modifying filesystem state."""
        try:
            data = json.loads(self.lock_path.read_text(encoding="utf-8"))
            return LockInfo.from_dict(data)
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            return None

    def _is_lock_info_valid(self, lock_info: LockInfo) -> bool:
        """Return whether an already-read lock still represents a live owner."""
        try:
            lock_time = datetime.fromisoformat(lock_info.timestamp)
        except (TypeError, ValueError):
            return False
        if datetime.now() > lock_time + timedelta(seconds=lock_info.timeout):
            return False
        if IS_WINDOWS:
            return self._is_process_alive_windows(lock_info.pid)
        return self._is_process_alive_posix(lock_info.pid)

    def _is_lock_valid(self) -> bool:
        """Check validity without deleting expired or malformed lock files."""
        lock_info = self._read_lock()
        return lock_info is not None and self._is_lock_info_valid(lock_info)

    def _is_process_alive_windows(self, pid: int) -> bool:
        """Verifica si un proceso existe en Windows"""
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if handle == 0:
                last_error = getattr(ctypes, "get_last_error", lambda: 0)()
                if last_error == 5:  # ERROR_ACCESS_DENIED: process exists, but is elevated.
                    return True
                if last_error == 87:  # ERROR_INVALID_PARAMETER: PID does not exist.
                    return False
                return True  # Unknown probe failure: never steal a possibly-live lock.
            kernel32.CloseHandle(handle)
            return True
        except Exception:
            return True

    def _is_process_alive_posix(self, pid: int) -> bool:
        """Verifica si un proceso existe en Unix"""
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError as exc:
            if exc.errno == errno.ESRCH:
                return False
            return True

    def _break_lock(self, expected: Optional[LockInfo] = None) -> bool:
        """Remove a stale lock only while it still matches the observed owner."""
        try:
            if expected is not None and self._read_lock() != expected:
                return False
            self.lock_path.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False

    def _malformed_lock_is_stale(self) -> bool:
        """Treat recent malformed content as an in-progress exclusive write."""
        try:
            age_seconds = time.time() - self.lock_path.stat().st_mtime
        except OSError:
            return False
        return age_seconds > self.DEFAULT_TIMEOUT

    def _try_create_exclusive(self, lock_info: LockInfo) -> bool:
        """Create the lock atomically; return False when another owner won."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            descriptor = os.open(self.lock_path, flags, 0o644)
        except FileExistsError:
            return False
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(lock_info.to_dict(), stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            try:
                self.lock_path.unlink()
            except OSError:
                pass
            raise
        return True

    def acquire(self, timeout: float = DEFAULT_TIMEOUT, blocking: bool = True) -> bool:
        """
        Intenta adquirir el lock.

        Args:
            timeout: Tiempo máximo de espera (segundos)
            blocking: Si False, retorna inmediatamente si no puede lockear

        Returns:
            True si el lock fue adquirido, False si no
        """
        if self._owned:
            return True  # Ya tenemos el lock

        start_time = time.monotonic()

        while True:
            observed = self._read_lock()
            if observed is None:
                if self.lock_path.exists() and self._malformed_lock_is_stale():
                    self._break_lock()
            elif not self._is_lock_info_valid(observed):
                self._break_lock(observed)

            candidate = LockInfo(
                instance_id=self.instance_id,
                pid=self.pid,
                timestamp=datetime.now().isoformat(),
                timeout=timeout,
                resource=str(self.resource_path),
            )
            try:
                if self._try_create_exclusive(candidate):
                    self._lock_info = candidate
                    self._owned = True
                    return True
            except OSError:
                return False

            # Verificar timeout
            if not blocking or (time.monotonic() - start_time) >= timeout:
                return False

            # Esperar antes de reintentar
            time.sleep(self.DEFAULT_POLL_INTERVAL)

    def release(self) -> bool:
        """
        Libera el lock si lo poseemos.

        Returns:
            True si el lock fue liberado, False si no lo poseíamos
        """
        if not self._owned:
            return False

        lock_info = self._read_lock()
        if lock_info is None or lock_info.instance_id != self.instance_id:
            return False
        if not self._break_lock(lock_info):
            return False
        self._owned = False
        self._lock_info = None
        return True

    def _cleanup_at_exit(self):
        """Limpieza automática al salir del programa"""
        if self._owned:
            self.release()

    def get_owner(self) -> Optional[LockInfo]:
        """
        Obtiene información del dueño actual del lock.

        Returns:
            LockInfo si hay un lock válido, None si no
        """
        return self._read_lock()

    def is_locked(self) -> bool:
        """Retorna True si el recurso está lockeado por alguien"""
        return self._is_lock_valid()

    def __enter__(self):
        """Context manager entry"""
        if not self.acquire():
            owner = self.get_owner()
            owner_info = f" (owned by {owner.instance_id})" if owner else ""
            raise LockTimeoutError(
                f"No se pudo adquirir lock para {self.resource_path}{owner_info}"
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        return False


class LockTimeoutError(Exception):
    """Error cuando no se puede adquirir un lock dentro del timeout"""

    pass


# Funciones de conveniencia


def acquire_lock(
    resource_path: str, timeout: float = 300.0, instance_id: Optional[str] = None
) -> Optional[FileLock]:
    """
    Adquiere un lock de forma sencilla.

    Args:
        resource_path: Ruta al recurso
        timeout: Timeout en segundos
        instance_id: ID de instancia (opcional)

    Returns:
        FileLock si se adquirió, None si no
    """
    lock = FileLock(resource_path, instance_id)
    if lock.acquire(timeout=timeout):
        return lock
    return None


def release_lock(lock: FileLock) -> bool:
    """
    Libera un lock.

    Args:
        lock: Instancia de FileLock

    Returns:
        True si se liberó correctamente
    """
    return lock.release()


@contextmanager
def lock_resource(
    resource_path: str, timeout: float = 300.0, instance_id: Optional[str] = None
):
    """
    Context manager para lockear un recurso.

    Uso:
        with lock_resource("archivo.txt", timeout=5.0) as lock:
            # código seguro
            pass
    """
    lock = FileLock(resource_path, instance_id)
    if not lock.acquire(timeout=timeout):
        owner = lock.get_owner()
        owner_info = f" (owned by {owner.instance_id})" if owner else ""
        raise LockTimeoutError(
            f"Timeout adquiriendo lock para {resource_path}{owner_info}"
        )

    try:
        yield lock
    finally:
        lock.release()


# CLI para testing
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="File Lock Utility")
    parser.add_argument("resource", help="Recurso a lockear")
    parser.add_argument(
        "--timeout", "-t", type=float, default=5.0, help="Timeout en segundos"
    )
    parser.add_argument("--instance-id", "-i", help="ID de instancia")
    parser.add_argument(
        "--action",
        "-a",
        choices=["acquire", "check", "force-release"],
        default="acquire",
        help="Acción a realizar",
    )

    args = parser.parse_args()

    lock = FileLock(args.resource, args.instance_id)

    if args.action == "acquire":
        print(f"Intentando lockear {args.resource} (timeout: {args.timeout}s)...")
        if lock.acquire(timeout=args.timeout):
            print(f"[OK] Lock adquirido por {lock.instance_id}")
            print("Presiona Enter para liberar...")
            input()
            lock.release()
            print("[UNLOCK] Lock liberado")
        else:
            owner = lock.get_owner()
            if owner:
                print(
                    f"[FAIL] No se pudo adquirir lock. Dueño: {owner.instance_id} (PID: {owner.pid})"
                )
            else:
                print("[FAIL] No se pudo adquirir lock (razón desconocida)")

    elif args.action == "check":
        owner = lock.get_owner()
        if owner:
            print(f"[LOCK] Lockeado por: {owner.instance_id}")
            print(f"   PID: {owner.pid}")
            print(f"   Desde: {owner.timestamp}")
            print(f"   Timeout: {owner.timeout}s")
        else:
            print("[UNLOCK] No está lockeado")

    elif args.action == "force-release":
        print(f"Forzando liberación de {args.resource}...")
        lock._break_lock()
        print("[OK] Lock forzado liberado")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
event-bridge.py - Sistema de eventos file-based para comunicación entre CLIs
Para FreakingJSON-PA Multi-CLI Framework

Este módulo implementa un sistema pub/sub usando archivos para permitir
comunicación en tiempo real entre múltiples instancias CLI sin requerir
servidores o sockets.

Uso:
    from event_bridge import EventBridge, EventType

    # Publicar evento
    bridge = EventBridge(instance_id="cli-001")
    bridge.publish(EventType.FILE_MODIFIED, {
        "file": "recordatorios.md",
        "change": "added task"
    })

    # Suscribirse a eventos
    def on_file_changed(event):
        print(f"Archivo modificado: {event.data['file']}")

    bridge.subscribe(EventType.FILE_MODIFIED, on_file_changed)
    bridge.start_listening()  # Inicia thread de escucha

Autor: FreakingJSON-PA Framework
Versión: 1.0.0
"""

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
import os
import json
import time
import uuid
import threading
from pathlib import Path
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, asdict
from queue import Queue, Empty


class EventType(Enum):
    """Tipos de eventos soportados"""

    # Eventos de sistema
    INSTANCE_JOINED = "instance_joined"  # Nueva CLI se unió
    INSTANCE_LEFT = "instance_left"  # CLI se desconectó
    INSTANCE_HEARTBEAT = "instance_heartbeat"  # Heartbeat de instancia

    # Eventos de archivos
    FILE_MODIFIED = "file_modified"  # Archivo modificado
    FILE_CONFLICT = "file_conflict"  # Conflicto detectado
    FILE_LOCKED = "file_locked"  # Archivo lockeado
    FILE_UNLOCKED = "file_unlocked"  # Archivo deslockeado

    # Eventos de sesión
    SESSION_CREATED = "session_created"  # Nueva sesión creada
    SESSION_UPDATED = "session_updated"  # Sesión actualizada
    SESSION_MERGED = "session_merged"  # Sesiones mergeadas

    # Eventos de usuario
    USER_NOTIFICATION = "user_notification"  # Notificación para usuario


@dataclass
class Event:
    """Representa un evento en el sistema"""

    id: str
    type: str
    timestamp: str
    source: str  # instance_id que generó el evento
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp,
            "source": self.source,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            id=data["id"],
            type=data["type"],
            timestamp=data["timestamp"],
            source=data["source"],
            data=data["data"],
        )

    @classmethod
    def create(
        cls, event_type: EventType, source: str, data: Dict[str, Any]
    ) -> "Event":
        """Factory para crear eventos nuevos"""
        return cls(
            id=str(uuid.uuid4())[:8],
            type=event_type.value,
            timestamp=datetime.now().isoformat(),
            source=source,
            data=data,
        )


class EventBridge:
    """
    Puente de eventos file-based para comunicación entre CLIs.

    Cada instancia escribe a un archivo de eventos compartido.
    Se usa un thread para polling eficiente de nuevos eventos.
    """

    DEFAULT_POLL_INTERVAL = 0.5  # 500ms
    EVENTS_FILE = "events.jsonl"
    MAX_EVENTS = 1000  # Rotación de eventos

    def __init__(self, instance_id: str, session_date: Optional[str] = None):
        """
        Args:
            instance_id: ID único de esta instancia CLI
            session_date: Fecha de sesión (default: hoy)
        """
        self.instance_id = instance_id
        self.session_date = session_date or datetime.now().strftime("%Y-%m-%d")

        # Directorio de eventos
        self.events_dir = Path("core/.context/sessions/.events")
        self.events_dir.mkdir(parents=True, exist_ok=True)

        # Archivo de eventos para hoy
        self.events_file = self.events_dir / f"{self.session_date}.jsonl"

        # Subscribers: {event_type: [callbacks]}
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._global_subscribers: List[Callable[[Event], None]] = []

        # Estado del listener
        self._listening = False
        self._listener_thread: Optional[threading.Thread] = None
        self._last_event_time: Optional[str] = None
        self._processed_events: set = set()

        # Queue para eventos entrantes (thread-safe)
        self._event_queue: Queue = Queue()
        self._worker_thread: Optional[threading.Thread] = None

        # Lock para operaciones de archivo
        self._file_lock = threading.Lock()

    def _get_events_file(self) -> Path:
        """Obtiene el archivo de eventos, creándolo si no existe"""
        if not self.events_file.exists():
            self.events_file.touch()
        return self.events_file

    def publish(self, event_type: EventType, data: Dict[str, Any]) -> Event:
        """
        Publica un evento al sistema.

        Args:
            event_type: Tipo de evento
            data: Datos del evento

        Returns:
            El evento creado
        """
        event = Event.create(event_type, self.instance_id, data)

        # Escribir al archivo (append)
        with self._file_lock:
            events_file = self._get_events_file()
            with open(events_file, "a", encoding="utf-8") as f:
                json_line = json.dumps(event.to_dict(), ensure_ascii=False)
                f.write(json_line + "\n")

        return event

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """
        Suscribe un callback a un tipo de evento específico.

        Args:
            event_type: Tipo de evento a escuchar
            callback: Función a llamar cuando ocurra el evento
        """
        event_type_str = (
            event_type.value if isinstance(event_type, EventType) else event_type
        )

        if event_type_str not in self._subscribers:
            self._subscribers[event_type_str] = []

        self._subscribers[event_type_str].append(callback)

    def subscribe_all(self, callback: Callable[[Event], None]):
        """
        Suscribe un callback a TODOS los eventos.

        Args:
            callback: Función a llamar para cualquier evento
        """
        self._global_subscribers.append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Desuscribe un callback"""
        event_type_str = (
            event_type.value if isinstance(event_type, EventType) else event_type
        )

        if event_type_str in self._subscribers:
            try:
                self._subscribers[event_type_str].remove(callback)
            except ValueError:
                pass

    def start_listening(self):
        """Inicia el thread de escucha de eventos"""
        if self._listening:
            return

        self._listening = True

        # Thread de polling
        self._listener_thread = threading.Thread(
            target=self._poll_events,
            daemon=True,
            name=f"EventBridge-{self.instance_id}",
        )
        self._listener_thread.start()

        # Thread de procesamiento
        self._worker_thread = threading.Thread(
            target=self._process_events,
            daemon=True,
            name=f"EventWorker-{self.instance_id}",
        )
        self._worker_thread.start()

        # Notificar unión
        self.publish(
            EventType.INSTANCE_JOINED,
            {"instance_id": self.instance_id, "timestamp": datetime.now().isoformat()},
        )

    def stop_listening(self):
        """Detiene el thread de escucha"""
        if not self._listening:
            return

        self._listening = False

        # Notificar salida
        self.publish(
            EventType.INSTANCE_LEFT,
            {"instance_id": self.instance_id, "timestamp": datetime.now().isoformat()},
        )

        # Esperar threads
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=1.0)

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

    def _poll_events(self):
        """Thread que hace polling del archivo de eventos"""
        while self._listening:
            try:
                # Leer nuevos eventos
                events = self._read_new_events()

                for event in events:
                    # Ignorar eventos propios (opcional, configurable)
                    if event.source != self.instance_id:
                        self._event_queue.put(event)

                # Pequeña pausa para no saturar CPU
                time.sleep(self.DEFAULT_POLL_INTERVAL)

            except Exception as e:
                # Log error pero continuar
                print(f"[EventBridge] Error en polling: {e}")
                time.sleep(self.DEFAULT_POLL_INTERVAL)

    def _read_new_events(self) -> List[Event]:
        """Lee eventos nuevos desde el archivo"""
        events = []

        try:
            events_file = self._get_events_file()

            with self._file_lock:
                with open(events_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            event = Event.from_dict(data)

                            # Evitar procesar el mismo evento dos veces
                            if event.id not in self._processed_events:
                                events.append(event)
                                self._processed_events.add(event.id)

                                # Mantener tamaño del set controlado
                                if len(self._processed_events) > self.MAX_EVENTS:
                                    self._processed_events.clear()

                        except json.JSONDecodeError:
                            continue

        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[EventBridge] Error leyendo eventos: {e}")

        return events

    def _process_events(self):
        """Thread que procesa eventos de la queue"""
        while self._listening:
            try:
                # Esperar evento con timeout
                event = self._event_queue.get(timeout=0.5)

                # Notificar a subscribers específicos
                if event.type in self._subscribers:
                    for callback in self._subscribers[event.type]:
                        try:
                            callback(event)
                        except Exception as e:
                            print(f"[EventBridge] Error en callback: {e}")

                # Notificar a subscribers globales
                for callback in self._global_subscribers:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"[EventBridge] Error en callback global: {e}")

                self._event_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                print(f"[EventBridge] Error procesando evento: {e}")

    def get_active_instances(self, timeout_seconds: int = 60) -> List[Dict[str, Any]]:
        """
        Obtiene lista de instancias activas basado en heartbeats recientes.

        Args:
            timeout_seconds: Segundos desde último heartbeat para considerar activa

        Returns:
            Lista de dicts con info de instancias
        """
        instances = {}
        cutoff_time = time.time() - timeout_seconds

        try:
            events_file = self._get_events_file()

            with self._file_lock:
                with open(events_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            event = Event.from_dict(data)

                            if event.type == EventType.INSTANCE_HEARTBEAT.value:
                                instance_id = event.data.get("instance_id")
                                if instance_id:
                                    instances[instance_id] = {
                                        "instance_id": instance_id,
                                        "last_heartbeat": event.timestamp,
                                        "model": event.data.get("model", "unknown"),
                                        "status": "active",
                                    }

                            elif event.type == EventType.INSTANCE_LEFT.value:
                                instance_id = event.data.get("instance_id")
                                if instance_id in instances:
                                    instances[instance_id]["status"] = "disconnected"

                        except (json.JSONDecodeError, KeyError):
                            continue

        except FileNotFoundError:
            pass

        # Filtrar solo activos recientes
        active = [i for i in instances.values() if i["status"] == "active"]

        return active

    def send_heartbeat(self, model: Optional[str] = None):
        """Envía un heartbeat para mantener la instancia como activa"""
        self.publish(
            EventType.INSTANCE_HEARTBEAT,
            {
                "instance_id": self.instance_id,
                "model": model or "unknown",
                "pid": os.getpid(),
                "timestamp": datetime.now().isoformat(),
            },
        )

    def __enter__(self):
        """Context manager entry"""
        self.start_listening()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_listening()
        return False


# Funciones de conveniencia


def notify_file_modified(
    file_path: str,
    change_description: str,
    instance_id: str,
    session_date: Optional[str] = None,
):
    """
    Notifica que un archivo fue modificado.

    Args:
        file_path: Ruta del archivo modificado
        change_description: Descripción del cambio
        instance_id: ID de la instancia
        session_date: Fecha de sesión (opcional)
    """
    bridge = EventBridge(instance_id, session_date)
    bridge.publish(
        EventType.FILE_MODIFIED,
        {
            "file": file_path,
            "change": change_description,
            "timestamp": datetime.now().isoformat(),
        },
    )


def notify_conflict(
    file_path: str,
    instances_involved: List[str],
    instance_id: str,
    session_date: Optional[str] = None,
):
    """
    Notifica un conflicto entre instancias.

    Args:
        file_path: Ruta del archivo en conflicto
        instances_involved: IDs de instancias involucradas
        instance_id: ID de la instancia reportando
        session_date: Fecha de sesión (opcional)
    """
    bridge = EventBridge(instance_id, session_date)
    bridge.publish(
        EventType.FILE_CONFLICT,
        {
            "file": file_path,
            "instances": instances_involved,
            "timestamp": datetime.now().isoformat(),
        },
    )


# CLI para testing
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Event Bridge Utility")
    parser.add_argument("--instance-id", "-i", required=True, help="ID de instancia")
    parser.add_argument(
        "--action",
        "-a",
        choices=["listen", "publish", "list-instances"],
        default="listen",
        help="Acción a realizar",
    )
    parser.add_argument("--event-type", "-t", help="Tipo de evento para publish")
    parser.add_argument("--data", "-d", help="Datos JSON para publish")
    parser.add_argument("--session-date", "-s", help="Fecha de sesión")

    args = parser.parse_args()

    if args.action == "listen":
        print(f"🔊 Iniciando escucha como {args.instance_id}...")
        print("Presiona Ctrl+C para salir\n")

        bridge = EventBridge(args.instance_id, args.session_date)

        def on_event(event):
            print(f"[{event.type}] desde {event.source}")
            print(f"  Datos: {json.dumps(event.data, indent=2)}")
            print()

        bridge.subscribe_all(on_event)
        bridge.start_listening()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[BYE] Deteniendo...")
            bridge.stop_listening()

    elif args.action == "publish":
        if not args.event_type:
            print("Error: --event-type requerido para publish")
            sys.exit(1)

        data = json.loads(args.data) if args.data else {}

        bridge = EventBridge(args.instance_id, args.session_date)
        event = bridge.publish(EventType(args.event_type), data)
        print(f"[OK] Evento publicado: {event.id}")

    elif args.action == "list-instances":
        bridge = EventBridge(args.instance_id, args.session_date)
        instances = bridge.get_active_instances()

        if instances:
            print(f"[INSTANCES] Instancias activas ({len(instances)}):")
            for inst in instances:
                print(f"  - {inst['instance_id']} ({inst['model']})")
                print(f"    Último heartbeat: {inst['last_heartbeat']}")
        else:
            print("No hay instancias activas")

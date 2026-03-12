#!/usr/bin/env python3
"""
Interaction Logger - PA Framework
=================================

Logger de interacciones para el framework FreakingJSON-PA.
Registra prompts, file operations, agent calls, etc. en formato JSONL.

Uso:
    python core/scripts/interaction-logger.py           # Inicializar logger
    python core/scripts/interaction-logger.py --stats   # Ver estadísticas
    python core/scripts/interaction-logger.py --archive # Archivar logs antiguos

Autor: FreakingJSON-PA Framework
Versión: 1.0.0 (BL-091)
"""

import argparse
import gzip
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONTEXT_DIR = REPO_ROOT / "core" / ".context"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
INTERACTIONS_DIR = KNOWLEDGE_DIR / "interactions"
ARCHIVE_DIR = INTERACTIONS_DIR / "archive"
CONFIG_FILE = KNOWLEDGE_DIR / "users" / "default" / "logging-config.md"

# Ensure directories exist
INTERACTIONS_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


class InteractionLogger:
    """Logger de interacciones con soporte para rotación y archive."""
    
    def __init__(self, config_override: Optional[Dict] = None):
        """
        Inicializar el logger.
        
        Args:
            config_override: Diccionario con configuración que overridea el archivo
        """
        self.config = self._load_config()
        if config_override:
            self.config.update(config_override)
        
        self.enabled = self.config.get('logging_enabled', True)
        self.log_level = self.config.get('log_level', 'prompt,file_write')
        self.anonymize = self.config.get('anonymize_sensitive', True)
        self.retention_days = self.config.get('retention_days', 30)
        
        self.log_levels = {
            'all': ['prompt', 'file_read', 'file_write', 'agent_call', 'skill_call', 'error'],
            'prompt': ['prompt'],
            'file_read': ['file_read'],
            'file_write': ['file_write'],
            'agent_call': ['agent_call'],
            'skill_call': ['skill_call'],
            'error': ['error'],
        }
    
    def _load_config(self) -> Dict:
        """Cargar configuración desde logging-config.md."""
        if not CONFIG_FILE.exists():
            return {
                'logging_enabled': True,
                'log_level': 'prompt,file_write',
                'anonymize_sensitive': True,
                'retention_days': 30
            }
        
        config = {}
        content = CONFIG_FILE.read_text(encoding='utf-8')
        
        # Parse YAML-like format from markdown code block
        in_code_block = False
        for line in content.split('\n'):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Parse value types
                if value.lower() == 'true':
                    config[key] = True
                elif value.lower() == 'false':
                    config[key] = False
                elif value.isdigit():
                    config[key] = int(value)
                else:
                    config[key] = value.strip('"\'')
        
        return config
    
    def _get_current_session(self) -> str:
        """Obtener sesión actual (fecha YYYY-MM-DD)."""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _get_log_file(self) -> Path:
        """Obtener archivo de log del día."""
        date_str = self._get_current_session()
        return INTERACTIONS_DIR / f"interactions-{date_str}.log"
    
    def _anonymize(self, text: str) -> str:
        """Anonimizar texto sensible si está configurado."""
        if not self.anonymize:
            return text
        
        # Patrones simples de anonimización
        import re
        
        # API keys (patrones comunes)
        text = re.sub(r'pk_[a-zA-Z0-9]+', '[REDACTED]', text)
        text = re.sub(r'sk_[a-zA-Z0-9]+', '[REDACTED]', text)
        text = re.sub(r'api[_-]?key[=:]\s*[\'"]?[a-zA-Z0-9]+[\'"]?', '[REDACTED]', text, flags=re.IGNORECASE)
        
        # URLs con tokens
        text = re.sub(r'https?://[^\s]*token=[^\s]*', '[URL]', text)
        text = re.sub(r'https?://[^\s]*key=[^\s]*', '[URL]', text)
        
        # Paths locales (Windows y Unix)
        text = re.sub(r'[A-Z]:\\[^"\']+', '[PATH]', text)
        text = re.sub(r'/home/[^/\s]+/', '[PATH]/', text)
        text = re.sub(r'/Users/[^/\s]+/', '[PATH]/', text)
        
        return text
    
    def _should_log(self, event_type: str) -> bool:
        """Verificar si el tipo de evento debe ser logueado."""
        if 'all' in self.log_level:
            return True
        
        levels = self.log_level.split(',')
        return event_type in levels
    
    def log(self, event_type: str, **kwargs) -> bool:
        """
        Registrar un evento.
        
        Args:
            event_type: Tipo de evento (prompt, file_write, etc.)
            **kwargs: Datos del evento
            
        Returns:
            True si se registró, False si logging está deshabilitado
        """
        if not self.enabled:
            return False
        
        if not self._should_log(event_type):
            return False
        
        # Construir evento
        event = {
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'session': self._get_current_session(),
        }
        
        # Agregar kwargs (anonimizando si es necesario)
        for key, value in kwargs.items():
            if isinstance(value, str) and self.anonymize:
                event[key] = self._anonymize(value)
            else:
                event[key] = value
        
        # Escribir al archivo del día
        log_file = self._get_log_file()
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"[InteractionLogger] Error writing to log: {e}", file=sys.stderr)
            return False
    
    def log_prompt(self, agent: str, model: str, prompt: str, 
                   tokens_in: int = 0, tokens_out: int = 0, 
                   duration_sec: float = 0.0, **extra) -> bool:
        """
        Registrar un prompt enviado a un LLM.
        
        Args:
            agent: Nombre del agente
            model: Modelo utilizado
            prompt: Prompt enviado (se trunca a 500 chars)
            tokens_in: Tokens de entrada
            tokens_out: Tokens de salida
            duration_sec: Duración en segundos
            extra: Datos adicionales
        """
        return self.log(
            'prompt',
            agent=agent,
            model=model,
            prompt_preview=prompt[:500] if len(prompt) > 500 else prompt,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_sec=duration_sec,
            **extra
        )
    
    def log_file_write(self, file_path: str, size_bytes: int, **extra) -> bool:
        """
        Registrar escritura de archivo.
        
        Args:
            file_path: Ruta del archivo
            size_bytes: Tamaño en bytes
            extra: Datos adicionales
        """
        return self.log(
            'file_write',
            file=file_path,
            size_bytes=size_bytes,
            **extra
        )
    
    def log_file_read(self, file_path: str, **extra) -> bool:
        """
        Registrar lectura de archivo.
        
        Args:
            file_path: Ruta del archivo
            extra: Datos adicionales
        """
        return self.log(
            'file_read',
            file=file_path,
            **extra
        )
    
    def log_agent_call(self, agent: str, action: str, **extra) -> bool:
        """
        Registrar llamada a agente.
        
        Args:
            agent: Nombre del agente
            action: Acción realizada
            extra: Datos adicionales
        """
        return self.log(
            'agent_call',
            agent=agent,
            action=action,
            **extra
        )
    
    def log_error(self, error: str, context: str = '', **extra) -> bool:
        """
        Registrar error.
        
        Args:
            error: Mensaje de error
            context: Contexto del error
            extra: Datos adicionales
        """
        return self.log(
            'error',
            error=error,
            context=context,
            **extra
        )
    
    def archive_old_logs(self, days: Optional[int] = None) -> int:
        """
        Archivar logs antiguos.
        
        Args:
            days: Días de retención (default: config)
            
        Returns:
            Cantidad de archivos archivados
        """
        if days is None:
            days = self.retention_days
        
        # Asegurar que days es int (no None)
        days_value: int = days if isinstance(days, int) else 30
        cutoff_date = datetime.now() - timedelta(days=float(days_value))
        archived_count = 0
        
        for log_file in INTERACTIONS_DIR.glob('interactions-*.log'):
            # Extraer fecha del nombre
            try:
                date_str = log_file.stem.replace('interactions-', '')
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    # Comprimir y mover a archive
                    archive_name = f"{log_file.stem}.log.gz"
                    archive_path = ARCHIVE_DIR / archive_name
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(archive_path, 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    # Eliminar original
                    log_file.unlink()
                    archived_count += 1
                    
            except Exception as e:
                print(f"[InteractionLogger] Error archiving {log_file}: {e}", file=sys.stderr)
        
        return archived_count
    
    def get_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener estadísticas del día.
        
        Args:
            date: Fecha en formato YYYY-MM-DD (default: hoy)
            
        Returns:
            Diccionario con estadísticas
        """
        if date is None:
            date = self._get_current_session()
        
        log_file = INTERACTIONS_DIR / f"interactions-{date}.log"
        if not log_file.exists():
            return {
                'total_events': 0,
                'by_type': {},
                'tokens_in': 0,
                'tokens_out': 0,
                'avg_duration': 0.0
            }
        
        stats = {
            'total_events': 0,
            'by_type': {},
            'tokens_in': 0,
            'tokens_out': 0,
            'durations': [],
            'agents': {},
            'models': {}
        }
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    stats['total_events'] += 1
                    
                    # Por tipo
                    event_type = event.get('event', 'unknown')
                    stats['by_type'][event_type] = stats['by_type'].get(event_type, 0) + 1
                    
                    # Tokens
                    if 'tokens_in' in event:
                        stats['tokens_in'] += event.get('tokens_in', 0)
                    if 'tokens_out' in event:
                        stats['tokens_out'] += event.get('tokens_out', 0)
                    
                    # Duración
                    if 'duration_sec' in event:
                        stats['durations'].append(event['duration_sec'])
                    
                    # Agentes
                    if 'agent' in event:
                        agent = event['agent']
                        stats['agents'][agent] = stats['agents'].get(agent, 0) + 1
                    
                    # Modelos
                    if 'model' in event:
                        model = event['model']
                        stats['models'][model] = stats['models'].get(model, 0) + 1
                    
                except json.JSONDecodeError:
                    continue
        
        # Calcular promedio
        stats['avg_duration'] = (
            sum(stats['durations']) / len(stats['durations']) 
            if stats['durations'] else 0.0
        )
        del stats['durations']  # No necesitamos la lista completa
        
        return stats


def print_stats(stats: Dict[str, Any], date: str):
    """Imprimir estadísticas en formato legible."""
    print(f"\n📊 Estadísticas de Logging - {date}")
    print("=" * 50)
    
    print(f"\nEventos totales: {stats['total_events']}")
    
    if stats['by_type']:
        print("\nPor tipo:")
        for event_type, count in sorted(stats['by_type'].items()):
            print(f"  - {event_type}: {count}")
    
    if stats['tokens_in'] > 0 or stats['tokens_out'] > 0:
        print(f"\nTokens:")
        print(f"  - Input: {stats['tokens_in']:,}")
        print(f"  - Output: {stats['tokens_out']:,}")
        print(f"  - Total: {stats['tokens_in'] + stats['tokens_out']:,}")
    
    if stats['avg_duration'] > 0:
        print(f"\nDuración promedio: {stats['avg_duration']:.1f}s")
    
    if stats['agents']:
        print("\nAgentes más usados:")
        for agent, count in sorted(stats['agents'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {agent}: {count}")
    
    if stats['models']:
        print("\nModelos más usados:")
        for model, count in sorted(stats['models'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {model}: {count}")
    
    print()


def main():
    """Función principal para CLI."""
    parser = argparse.ArgumentParser(description='Interaction Logger - FreakingJSON-PA')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas del día')
    parser.add_argument('--archive', action='store_true', help='Archivar logs antiguos')
    parser.add_argument('--days', type=int, help='Días de retención para archive')
    parser.add_argument('--date', type=str, help='Fecha para estadísticas (YYYY-MM-DD)')
    parser.add_argument('--init', action='store_true', help='Inicializar logger (crear config)')
    
    args = parser.parse_args()
    
    logger = InteractionLogger()
    
    if args.init:
        print("📝 Inicializando Interaction Logger...")
        print(f"   Config: {CONFIG_FILE}")
        print(f"   Logs: {INTERACTIONS_DIR}")
        print(f"   Archive: {ARCHIVE_DIR}")
        print("\n✅ Logger inicializado. Editar logging-config.md para configurar.")
        return 0
    
    if args.stats:
        date = args.date or logger._get_current_session()
        stats = logger.get_stats(date)
        print_stats(stats, date)
        return 0
    
    if args.archive:
        days = args.days if args.days else None
        archived = logger.archive_old_logs(days)
        print(f"📦 Archivos archivados: {archived}")
        return 0
    
    # Sin argumentos: mostrar ayuda
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())

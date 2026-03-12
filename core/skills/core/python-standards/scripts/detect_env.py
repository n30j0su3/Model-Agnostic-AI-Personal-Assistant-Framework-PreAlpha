#!/usr/bin/env python3
"""
Environment Detector - Detecta si es seguro usar emojis en el entorno actual.

Uso:
    from detect_env import should_use_emojis, get_safe_prefix

    if should_use_emojis():
        print(f"{get_safe_prefix('success')} Operación exitosa")
    else:
        print(f"{get_safe_prefix('success')} Operación exitosa")

O integrar al inicio de cualquier script CLI:

    import detect_env
    USE_EMOJIS = detect_env.should_use_emojis()

    def log_success(msg):
        prefix = "✅" if USE_EMOJIS else "[OK]"
        print(f"{prefix} {msg}")
"""

import platform
import sys
from typing import Dict


def should_use_emojis() -> bool:
    """
    Detecta si el entorno actual soporta emojis de forma segura.

    Returns:
        True si es seguro usar emojis, False en caso contrario.
    """
    # En Linux y macOS generalmente es seguro
    if platform.system() != "Windows":
        return True

    # En Windows, verificar el code page
    try:
        # Usar ctypes para obtener el code page de la consola
        import ctypes

        kernel32 = ctypes.windll.kernel32
        code_page = kernel32.GetConsoleOutputCP()

        # 65001 es UTF-8, el único code page que soporta emojis correctamente
        return code_page == 65001
    except Exception:
        # Si hay algún error, asumir que no es seguro
        return False


def get_safe_prefix(prefix_type: str = "info") -> str:
    """
    Retorna un prefijo seguro según el tipo y el entorno.

    Args:
        prefix_type: Tipo de prefijo ('success', 'error', 'warning', 'info')

    Returns:
        Prefijo apropiado (emoji o ASCII según el entorno)
    """
    emojis: Dict[str, str] = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "arrow": "➜",
        "bullet": "•",
        "check": "✓",
        "cross": "✗",
    }

    ascii_fallbacks: Dict[str, str] = {
        "success": "[OK]",
        "error": "[ERROR]",
        "warning": "[WARN]",
        "info": "[INFO]",
        "arrow": "->",
        "bullet": "-",
        "check": "[X]",
        "cross": "[ ]",
    }

    if should_use_emojis():
        return emojis.get(prefix_type, "[INFO]")
    else:
        return ascii_fallbacks.get(prefix_type, "[INFO]")


def print_safe(message: str, prefix_type: str = "info") -> None:
    """
    Imprime un mensaje con prefijo seguro automáticamente.

    Args:
        message: Mensaje a imprimir
        prefix_type: Tipo de prefijo ('success', 'error', 'warning', 'info')
    """
    prefix = get_safe_prefix(prefix_type)
    print(f"{prefix} {message}")


def configure_stdout() -> None:
    """
    Configura stdout para UTF-8 si es posible.
    Útil llamar al inicio de scripts CLI.
    """
    try:
        # Intentar configurar UTF-8 en Windows
        if platform.system() == "Windows":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # Intentar forzar UTF-8
            kernel32.SetConsoleOutputCP(65001)

        # Reconfigurar stdout para UTF-8
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # Si falla, continuar con la configuración actual
        pass


class SafePrinter:
    """
    Clase helper para imprimir mensajes con prefijos seguros.

    Uso:
        printer = SafePrinter()
        printer.success("Operación exitosa")
        printer.error("Algo falló")
        printer.warning("Advertencia")
        printer.info("Información")
    """

    def __init__(self):
        self._use_emojis = should_use_emojis()

    def _print(self, msg: str, prefix_type: str) -> None:
        prefix = get_safe_prefix(prefix_type)
        print(f"{prefix} {msg}")

    def success(self, msg: str) -> None:
        self._print(msg, "success")

    def error(self, msg: str) -> None:
        self._print(msg, "error")

    def warning(self, msg: str) -> None:
        self._print(msg, "warning")

    def info(self, msg: str) -> None:
        self._print(msg, "info")


# Ejemplo de uso si se ejecuta directamente
if __name__ == "__main__":
    print(f"Detectando entorno...")
    print(f"Plataforma: {platform.system()}")
    print(f"Code page: ", end="")

    if platform.system() == "Windows":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            code_page = kernel32.GetConsoleOutputCP()
            print(f"{code_page} ({'UTF-8' if code_page == 65001 else 'No UTF-8'})")
        except Exception as e:
            print(f"Error al detectar: {e}")
    else:
        print("N/A (No Windows)")

    print(f"\nEmojis soportados: {should_use_emojis()}")
    print(f"\nEjemplos de prefijos:")

    for ptype in ["success", "error", "warning", "info"]:
        prefix = get_safe_prefix(ptype)
        print(f"  {ptype}: {prefix} Mensaje de ejemplo")

    print(f"\nUsando SafePrinter:")
    printer = SafePrinter()
    printer.success("Esto es un éxito")
    printer.error("Esto es un error")
    printer.warning("Esto es una advertencia")
    printer.info("Esto es información")

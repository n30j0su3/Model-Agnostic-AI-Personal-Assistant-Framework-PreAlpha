#!/usr/bin/env python3
"""
Tests de Validación - sync-prealpha-optimized.py
===============================================

Suite de tests para verificar las mejoras implementadas.

Ejecución:
    python test_sync_prealpha_optimized.py
    python test_sync_prealpha_optimized.py -v  # Verbose
"""

import os
import sys
import shutil
import tempfile
import unittest
import importlib.util
from pathlib import Path
from datetime import datetime

# Cargar el script con guiones usando importlib
SCRIPT_PATH = Path(__file__).parent / "sync-prealpha-optimized.py"

try:
    spec = importlib.util.spec_from_file_location("sync_optimized", SCRIPT_PATH)
    sync_module = importlib.util.module_from_spec(spec)
    sys.modules["sync_optimized"] = sync_module
    spec.loader.exec_module(sync_module)

    # Importar clases y funciones
    FileCategory = sync_module.FileCategory
    FileOperation = sync_module.FileOperation
    CopyResult = sync_module.CopyResult
    ProgressTracker = sync_module.ProgressTracker
    FileCopyManager = sync_module.FileCopyManager
    ExtendedSyncReporter = sync_module.ExtendedSyncReporter
    validate_critical_resources = sync_module.validate_critical_resources
    should_include_for_skill = sync_module.should_include_for_skill
    calculate_hash = sync_module.calculate_hash
    PROTECTED_DIRS = sync_module.PROTECTED_DIRS
    CRITICAL_RESOURCES = sync_module.CRITICAL_RESOURCES

    IMPORT_OK = True
except Exception as e:
    print(f"[ERROR] No se pudo importar el script: {e}")
    IMPORT_OK = False


class TestFileCategory(unittest.TestCase):
    """Tests para categorización de archivos"""

    def test_skill_category(self):
        """Detecta archivos de skills"""
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("core/skills/test/manifest.json"),
            FileCategory.SKILL,
        )
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("skills/dashboard/main.py"),
            FileCategory.SKILL,
        )

    def test_agent_category(self):
        """Detecta archivos de agentes"""
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("core/agents/pa-assistant.md"),
            FileCategory.AGENT,
        )
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("agents/test-agent.yaml"),
            FileCategory.AGENT,
        )

    def test_docs_category(self):
        """Detecta documentación"""
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("docs/readme.md"), FileCategory.DOCS
        )
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("README.md"), FileCategory.DOCS
        )

    def test_config_category(self):
        """Detecta configuraciones"""
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("config.json"), FileCategory.CONFIG
        )
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("settings.yaml"), FileCategory.CONFIG
        )

    def test_script_category(self):
        """Detecta scripts"""
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("scripts/test.py"),
            FileCategory.SCRIPT,
        )
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("run.py"), FileCategory.SCRIPT
        )

    def test_other_category(self):
        """Detecta archivos varios"""
        self.assertEqual(
            ExtendedSyncReporter.get_file_category("random_file.txt"),
            FileCategory.OTHER,
        )


class TestProgressTracker(unittest.TestCase):
    """Tests para tracking de progreso"""

    def test_initialization(self):
        """Inicialización correcta"""
        tracker = ProgressTracker(total_items=100)
        self.assertEqual(tracker.total_items, 100)
        self.assertEqual(tracker.processed_items, 0)
        self.assertEqual(tracker.total_bytes, 0)

    def test_update_progress(self):
        """Actualización de progreso"""
        tracker = ProgressTracker(total_items=100)
        tracker.update(bytes_processed=1024)
        self.assertEqual(tracker.processed_items, 1)
        self.assertEqual(tracker.total_bytes, 1024)

    def test_progress_percentage(self):
        """Cálculo de porcentaje"""
        tracker = ProgressTracker(total_items=100)
        self.assertEqual(tracker.get_progress_percentage(), 0.0)

        for _ in range(25):
            tracker.update()
        self.assertEqual(tracker.get_progress_percentage(), 25.0)

    def test_format_bytes(self):
        """Formateo de bytes"""
        reporter = ExtendedSyncReporter()
        self.assertEqual(reporter.format_bytes(512), "512.0 B")
        self.assertEqual(reporter.format_bytes(1536), "1.5 KB")
        self.assertEqual(reporter.format_bytes(1572864), "1.5 MB")


class TestFileCopyManager(unittest.TestCase):
    """Tests para gestor de copias"""

    def setUp(self):
        """Crea directorio temporal para tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.src_file = Path(self.temp_dir) / "source.txt"
        self.dest_file = Path(self.temp_dir) / "dest.txt"

        # Crear archivo fuente
        self.src_file.write_text("Test content")

    def tearDown(self):
        """Limpia directorio temporal"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_successful_copy(self):
        """Copia exitosa de archivo"""
        if not IMPORT_OK:
            self.skipTest("Import failed")

        manager = FileCopyManager()
        result = manager.copy_file(self.src_file, self.dest_file)

        self.assertTrue(result.success)
        self.assertTrue(self.dest_file.exists())
        self.assertEqual(result.bytes_copied, len("Test content"))

    def test_copy_preserves_metadata(self):
        """Copia preserva metadatos"""
        if not IMPORT_OK:
            self.skipTest("Import failed")

        manager = FileCopyManager()
        result = manager.copy_file(
            self.src_file, self.dest_file, preserve_metadata=True
        )

        self.assertTrue(result.success)
        # Verificar que el archivo existe
        self.assertTrue(self.dest_file.exists())

    def test_failed_copy_nonexistent(self):
        """Manejo de error: archivo no existe"""
        if not IMPORT_OK:
            self.skipTest("Import failed")

        manager = FileCopyManager()
        nonexistent = Path(self.temp_dir) / "nonexistent.txt"
        result = manager.copy_file(nonexistent, self.dest_file)

        self.assertFalse(result.success)
        self.assertIn("no encontrado", result.error_message.lower())

    def test_copy_stats(self):
        """Estadísticas de copia"""
        if not IMPORT_OK:
            self.skipTest("Import failed")

        manager = FileCopyManager()
        manager.copy_file(self.src_file, self.dest_file)

        stats = manager.get_stats()
        self.assertEqual(stats["successful"], 1)
        self.assertEqual(stats["failed"], 0)


class TestSkillFiltering(unittest.TestCase):
    """Tests para filtrado por skill"""

    def test_skill_file_detection(self):
        """Detecta archivos de skill específica"""
        self.assertTrue(
            should_include_for_skill(
                "core/skills/dashboard-pro/main.py", "dashboard-pro"
            )
        )
        self.assertTrue(
            should_include_for_skill(
                "skills/dashboard-pro/manifest.json", "dashboard-pro"
            )
        )

    def test_related_file_detection(self):
        """Detecta archivos relacionados"""
        self.assertTrue(
            should_include_for_skill("docs/dashboard-pro-guide.md", "dashboard-pro")
        )

    def test_config_always_included(self):
        """Configuraciones siempre incluidas"""
        self.assertTrue(should_include_for_skill("core/config.json", "any-skill"))
        self.assertTrue(should_include_for_skill("core/config.txt", "any-skill"))

    def test_other_skills_excluded(self):
        """Excluye otras skills"""
        self.assertFalse(
            should_include_for_skill("core/skills/other-skill/main.py", "dashboard-pro")
        )


class TestProtectedDirs(unittest.TestCase):
    """Tests para directorios protegidos"""

    def test_local_dirs_included(self):
        """Directorios _local/ están protegidos"""
        self.assertIn("core/agents/subagents/_local", PROTECTED_DIRS)
        self.assertIn("core/skills/_local", PROTECTED_DIRS)
        self.assertIn("core/.context/workspaces", PROTECTED_DIRS)

    def test_sessions_protected(self):
        """Sesiones están protegidas"""
        self.assertIn("core/.context/sessions", PROTECTED_DIRS)

    def test_codebase_protected(self):
        """Codebase está protegido"""
        self.assertIn("core/.context/codebase", PROTECTED_DIRS)


class TestCriticalResources(unittest.TestCase):
    """Tests para recursos críticos"""

    def test_master_md_critical(self):
        """MASTER.md es crítico"""
        self.assertIn("core/.context/MASTER.md", CRITICAL_RESOURCES)

    def test_navigation_md_critical(self):
        """navigation.md es crítico"""
        self.assertIn("core/.context/navigation.md", CRITICAL_RESOURCES)

    def test_pa_assistant_critical(self):
        """pa-assistant.md es crítico"""
        self.assertIn("core/agents/pa-assistant.md", CRITICAL_RESOURCES)


class TestExtendedReporter(unittest.TestCase):
    """Tests para reporter extendido"""

    def test_bytes_tracking(self):
        """Tracking de bytes transferidos"""
        reporter = ExtendedSyncReporter()
        reporter.add("test.txt", 1024)
        reporter.modify("test2.txt", 2048)

        self.assertEqual(reporter.total_bytes_transferred, 3072)

    def test_elapsed_time(self):
        """Tiempo transcurrido"""
        import time

        reporter = ExtendedSyncReporter()
        time.sleep(0.1)  # Pequeña pausa

        elapsed = reporter.get_elapsed_time()
        self.assertTrue(len(elapsed) > 0)

    def test_categorized_operations(self):
        """Operaciones categorizadas"""
        reporter = ExtendedSyncReporter()

        # Agregar archivos de diferentes categorías
        reporter.add("core/skills/test/main.py", 1000)
        reporter.add("core/agents/agent.md", 500)
        reporter.add("docs/readme.md", 200)

        # Verificar que se categorizaron
        self.assertEqual(len(reporter.added), 3)

        # Verificar categorías
        categories = [op.category for op in reporter.added]
        self.assertIn(FileCategory.SKILL, categories)
        self.assertIn(FileCategory.AGENT, categories)
        self.assertIn(FileCategory.DOCS, categories)


class TestHashCalculation(unittest.TestCase):
    """Tests para cálculo de hash"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_file.write_text("Test content for hashing")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_hash_generation(self):
        """Generación de hash consistente"""
        hash1 = calculate_hash(self.test_file)
        hash2 = calculate_hash(self.test_file)

        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 32)  # MD5 = 32 caracteres hex

    def test_hash_changes_with_content(self):
        """Hash cambia con contenido diferente"""
        hash1 = calculate_hash(self.test_file)

        # Modificar contenido
        self.test_file.write_text("Different content")
        hash2 = calculate_hash(self.test_file)

        self.assertNotEqual(hash1, hash2)

    def test_hash_nonexistent_file(self):
        """Hash de archivo inexistente retorna vacío"""
        nonexistent = Path(self.temp_dir) / "nonexistent.txt"
        result = calculate_hash(nonexistent)

        self.assertEqual(result, "")


class TestIntegration(unittest.TestCase):
    """Tests de integración"""

    def setUp(self):
        """Crea estructura de directorios de prueba"""
        self.temp_base = tempfile.mkdtemp(prefix="base_")
        self.temp_dest = tempfile.mkdtemp(prefix="dest_")

        # Crear estructura base
        base_path = Path(self.temp_base)
        (base_path / "core" / "skills" / "test-skill").mkdir(parents=True)
        (base_path / "core" / "skills" / "test-skill" / "main.py").write_text(
            "print('test')"
        )
        (base_path / "core" / ".context").mkdir(parents=True)
        (base_path / "core" / ".context" / "MASTER.md").write_text("# Master")

        # Crear estructura destino
        dest_path = Path(self.temp_dest)
        (dest_path / "core" / ".context").mkdir(parents=True)

    def tearDown(self):
        """Limpia estructura de prueba"""
        shutil.rmtree(self.temp_base, ignore_errors=True)
        shutil.rmtree(self.temp_dest, ignore_errors=True)

    def test_critical_resource_validation(self):
        """Validación de recursos críticos"""
        if not IMPORT_OK:
            self.skipTest("Import failed")

        reporter = ExtendedSyncReporter()

        # Crear recurso crítico faltante
        dest_path = Path(self.temp_dest)
        (dest_path / "core" / ".context" / "MASTER.md").write_text("# Master")
        (dest_path / "core" / ".context" / "navigation.md").write_text("# Nav")
        (dest_path / "core" / "agents").mkdir(parents=True)
        (dest_path / "core" / "agents" / "pa-assistant.md").write_text("# Assistant")

        result = validate_critical_resources(dest_path, reporter)
        self.assertTrue(result)


def run_tests():
    """Ejecuta todos los tests"""
    print("=" * 70)
    print("TESTS DE VALIDACIÓN - sync-prealpha-optimized.py")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Import: {'OK' if IMPORT_OK else 'FALLIDO'}")
    print("=" * 70)

    if not IMPORT_OK:
        print("\n[!] No se pudieron importar los módulos del script.")
        print(
            "    Asegúrate de que sync_prealpha_optimized.py esté en el mismo directorio."
        )
        return False

    # Ejecutar tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS")
    print("=" * 70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallidos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

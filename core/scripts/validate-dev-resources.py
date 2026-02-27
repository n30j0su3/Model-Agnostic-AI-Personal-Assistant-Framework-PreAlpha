#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de Recursos DEV - Pre-Sync Validation
Framework: FreakingJSON-PA
Purpose: Verificar recursos criticos antes de sincronizacion BASE -> DEV
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class ResourceStatus:
    """Estado de un recurso individual"""

    path: str
    exists: bool
    size_bytes: int
    md5_hash: Optional[str]
    is_directory: bool
    last_modified: Optional[str]


@dataclass
class ValidationReport:
    """Reporte completo de validacion"""

    timestamp: str
    dev_path: str
    base_path: Optional[str]
    total_resources: int
    present_resources: List[ResourceStatus]
    missing_resources: List[str]
    new_in_base: List[str]
    potential_conflicts: List[str]
    summary: Dict


class DEVResourceValidator:
    """Validador de recursos criticos DEV"""

    # Recursos criticos que NO deben perderse
    CRITICAL_RESOURCES = [
        # Agentes locales
        "core/agents/subagents/_local/maaji/maaji-master.md",
        # Skills locales (4 skills de Maaji)
        "core/skills/_local/maaji/atribucion/SKILL.md",
        "core/skills/_local/maaji/checkout-con-evento/SKILL.md",
        "core/skills/_local/maaji/checkout-sin-evento/SKILL.md",
        "core/skills/_local/maaji/klaviyo-extract/SKILL.md",
        # Workspaces
        "workspaces/professional/projects/Maaji",
        "workspaces/personal",
        "workspaces/development",
        # Contexto especifico
        "core/.context/workspaces/maaji.md",
        # Documentacion
        "docs/MAAJI-PROMOTION-GUIDE.md",
    ]

    def __init__(self, dev_path: str, base_path: Optional[str] = None):
        self.dev_path = Path(dev_path)
        self.base_path = Path(base_path) if base_path else None
        self.report: Optional[ValidationReport] = None

    def calculate_md5(self, file_path: Path) -> Optional[str]:
        """Calcula hash MD5 de un archivo"""
        if not file_path.is_file():
            return None
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"  [WARN] Error calculando MD5 para {file_path}: {e}")
            return None

    def check_resource(self, relative_path: str) -> ResourceStatus:
        """Verifica un recurso individual"""
        full_path = self.dev_path / relative_path
        exists = full_path.exists()

        if exists:
            is_dir = full_path.is_dir()
            size = 0 if is_dir else full_path.stat().st_size
            md5 = None if is_dir else self.calculate_md5(full_path)
            mtime = datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()
        else:
            is_dir = False
            size = 0
            md5 = None
            mtime = None

        return ResourceStatus(
            path=relative_path,
            exists=exists,
            size_bytes=size,
            md5_hash=md5,
            is_directory=is_dir,
            last_modified=mtime,
        )

    def detect_new_in_base(self) -> List[str]:
        """Detecta recursos nuevos en BASE que podrian llegar al sync"""
        if not self.base_path or not self.base_path.exists():
            return []

        new_resources = []

        # Verificar estructuras comunes que podrian ser nuevas
        base_dirs_to_check = [
            "core/agents/subagents/_local",
            "core/skills/_local",
            "workspaces",
        ]

        for check_dir in base_dirs_to_check:
            base_dir = self.base_path / check_dir
            dev_dir = self.dev_path / check_dir

            if base_dir.exists():
                for item in base_dir.rglob("*"):
                    if item.is_file():
                        # Calcular path relativo
                        try:
                            rel_path = item.relative_to(self.base_path)
                            dev_item = dev_dir / rel_path.relative_to(Path(check_dir))
                            if not dev_item.exists():
                                new_resources.append(str(rel_path))
                        except ValueError:
                            pass

        return new_resources

    def detect_conflicts(self, present_resources: List[ResourceStatus]) -> List[str]:
        """Detecta potenciales conflictos entre DEV y BASE"""
        conflicts = []

        if not self.base_path or not self.base_path.exists():
            return conflicts

        for resource in present_resources:
            base_file = self.base_path / resource.path
            dev_file = self.dev_path / resource.path

            if base_file.exists() and dev_file.exists() and not resource.is_directory:
                base_md5 = self.calculate_md5(base_file)
                if base_md5 != resource.md5_hash:
                    conflicts.append(resource.path)

        return conflicts

    def validate(self) -> ValidationReport:
        """Ejecuta validacion completa"""
        print("[INIT] Iniciando validacion de recursos DEV...")
        print(f"[PATH] DEV Path: {self.dev_path}")
        if self.base_path:
            print(f"[PATH] BASE Path: {self.base_path}")
        print()

        present = []
        missing = []

        # Verificar cada recurso critico
        print("[CHECK] Verificando recursos criticos...")
        for resource_path in self.CRITICAL_RESOURCES:
            status = self.check_resource(resource_path)
            if status.exists:
                present.append(status)
                icon = "[DIR]" if status.is_directory else "[FILE]"
                size_str = (
                    f"{status.size_bytes:,} bytes"
                    if not status.is_directory
                    else "<DIR>"
                )
                print(f"  [OK] {icon} {resource_path} ({size_str})")
            else:
                missing.append(resource_path)
                print(f"  [MISSING] {resource_path} - NO ENCONTRADO")

        print()

        # Detectar recursos nuevos en BASE
        new_in_base = []
        if self.base_path:
            print("[SCAN] Detectando recursos nuevos en BASE...")
            new_in_base = self.detect_new_in_base()
            if new_in_base:
                for new_res in new_in_base[:10]:  # Limitar a 10 para no saturar
                    print(f"  [NEW] {new_res}")
                if len(new_in_base) > 10:
                    print(f"  ... y {len(new_in_base) - 10} mas")
            else:
                print("  [INFO] No se detectaron recursos nuevos significativos")
            print()

        # Detectar conflictos
        conflicts = []
        if self.base_path:
            print("[CHECK] Verificando potenciales conflictos...")
            conflicts = self.detect_conflicts(present)
            if conflicts:
                for conflict in conflicts:
                    print(f"  [CONFLICT] {conflict} (diferente en DEV y BASE)")
            else:
                print("  [OK] No se detectaron conflictos")
            print()

        # Generar resumen
        summary = {
            "total_critical": len(self.CRITICAL_RESOURCES),
            "present_count": len(present),
            "missing_count": len(missing),
            "new_in_base_count": len(new_in_base),
            "conflicts_count": len(conflicts),
            "integrity_score": len(present) / len(self.CRITICAL_RESOURCES) * 100,
        }

        self.report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            dev_path=str(self.dev_path),
            base_path=str(self.base_path) if self.base_path else None,
            total_resources=len(self.CRITICAL_RESOURCES),
            present_resources=present,
            missing_resources=missing,
            new_in_base=new_in_base,
            potential_conflicts=conflicts,
            summary=summary,
        )

        return self.report

    def save_json_state(self, output_path: str = "dev-resources-state.json"):
        """Guarda el estado actual en JSON"""
        if not self.report:
            raise ValueError("Debe ejecutar validate() primero")

        data = {
            "timestamp": self.report.timestamp,
            "dev_path": self.report.dev_path,
            "base_path": self.report.base_path,
            "resources": [asdict(r) for r in self.report.present_resources],
            "missing": self.report.missing_resources,
            "new_in_base": self.report.new_in_base,
            "conflicts": self.report.potential_conflicts,
            "summary": self.report.summary,
        }

        output_file = Path(output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[SAVED] Estado guardado en: {output_file}")
        return output_file

    def generate_markdown_report(self, output_path: str = "DEV-VALIDATION-REPORT.md"):
        """Genera reporte en formato Markdown"""
        if not self.report:
            raise ValueError("Debe ejecutar validate() primero")

        lines = [
            "# Reporte de Validacion DEV - Pre-Sync",
            "",
            f"**Fecha:** {self.report.timestamp}",
            f"**DEV Path:** `{self.report.dev_path}`",
            f"**BASE Path:** `{self.report.base_path or 'N/A'}`",
            "",
            "---",
            "",
            "## Resumen Ejecutivo",
            "",
            f"- **Recursos criticos totales:** {self.report.summary['total_critical']}",
            f"- **Recursos presentes:** [OK] {self.report.summary['present_count']}",
            f"- **Recursos faltantes:** [MISSING] {self.report.summary['missing_count']}",
            f"- **Nuevos en BASE:** [NEW] {self.report.summary['new_in_base_count']}",
            f"- **Conflictos potenciales:** [CONFLICT] {self.report.summary['conflicts_count']}",
            f"- **Score de integridad:** {self.report.summary['integrity_score']:.1f}%",
            "",
            "---",
            "",
            "## Recursos Presentes",
            "",
            "| Recurso | Tipo | Tamaño | MD5 |",
            "|---------|------|--------|-----|",
        ]

        for resource in sorted(self.report.present_resources, key=lambda x: x.path):
            tipo = "[DIR]" if resource.is_directory else "[FILE]"
            size = "-" if resource.is_directory else f"{resource.size_bytes:,} bytes"
            md5 = resource.md5_hash[:8] + "..." if resource.md5_hash else "-"
            lines.append(f"| `{resource.path}` | {tipo} | {size} | {md5} |")

        if self.report.missing_resources:
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## Recursos Faltantes",
                    "",
                    "Los siguientes recursos criticos NO fueron encontrados:",
                    "",
                ]
            )
            for missing in self.report.missing_resources:
                lines.append(f"- [MISSING] `{missing}`")

        if self.report.new_in_base:
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## Recursos Nuevos en BASE",
                    "",
                    "Estos recursos existen en BASE pero no en DEV (llegaran con el sync):",
                    "",
                ]
            )
            for new in self.report.new_in_base[:20]:  # Limitar a 20
                lines.append(f"- [NEW] `{new}`")
            if len(self.report.new_in_base) > 20:
                lines.append(f"- ... y {len(self.report.new_in_base) - 20} mas")

        if self.report.potential_conflicts:
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## Conflictos Potenciales",
                    "",
                    "Estos archivos difieren entre DEV y BASE:",
                    "",
                ]
            )
            for conflict in self.report.potential_conflicts:
                lines.append(f"- [CONFLICT] `{conflict}` (modificado en ambos lados)")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Recomendaciones para Sync Seguro",
                "",
            ]
        )

        if self.report.summary["missing_count"] > 0:
            lines.append(
                "1. [WARNING] **ATENCION CRITICA:** Existen recursos faltantes. Verificar antes de sync."
            )

        if self.report.summary["conflicts_count"] > 0:
            lines.append(
                "2. [WARNING] **RESOLVER CONFLICTOS:** Archivos modificados en ambos lados requieren merge manual."
            )

        lines.extend(
            [
                "3. [OK] Realizar backup de DEV antes del sync",
                "4. [OK] Verificar que los agentes locales de Maaji no se sobrescriban",
                "5. [OK] Confirmar que las 4 skills de Maaji permanezcan intactas",
                "6. [OK] Validar workspaces de professional/personal/development post-sync",
                "",
                "---",
                "",
                "*Reporte generado automaticamente por validate-dev-resources.py*",
            ]
        )

        output_file = Path(output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"[SAVED] Reporte Markdown guardado en: {output_file}")
        return output_file


def main():
    """Funcion principal"""
    # Detectar rutas
    default_dev = r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_DEV"
    default_base = r"C:\ACTUAL\FreakingJSON-pa\Pa_Pre_alpha_Opus_4_6_BASE"

    # Permitir override por argumentos
    dev_path = sys.argv[1] if len(sys.argv) > 1 else default_dev
    base_path = sys.argv[2] if len(sys.argv) > 2 else default_base

    # Verificar que DEV existe
    if not Path(dev_path).exists():
        print(f"[ERROR] DEV path no existe: {dev_path}")
        sys.exit(1)

    # Crear validador
    validator = DEVResourceValidator(
        dev_path, base_path if Path(base_path).exists() else None
    )

    # Ejecutar validacion
    report = validator.validate()

    print("=" * 60)
    print("RESUMEN DE VALIDACION")
    print("=" * 60)
    print(f"  Total recursos criticos: {report.summary['total_critical']}")
    print(f"  [OK] Presentes: {report.summary['present_count']}")
    print(f"  [MISSING] Faltantes: {report.summary['missing_count']}")
    print(f"  [NEW] Nuevos en BASE: {report.summary['new_in_base_count']}")
    print(f"  [CONFLICT] Conflictos: {report.summary['conflicts_count']}")
    print(f"  [SCORE] Integridad: {report.summary['integrity_score']:.1f}%")
    print("=" * 60)

    # Guardar archivos
    validator.save_json_state("dev-resources-state.json")
    validator.generate_markdown_report("DEV-VALIDATION-REPORT.md")

    # Recomendaciones finales
    print()
    print("RECOMENDACIONES:")
    if report.summary["missing_count"] > 0:
        print("  [WARNING] URGENTE: Existen recursos criticos faltantes")
    if report.summary["conflicts_count"] > 0:
        print("  [WARNING] ATENCION: Hay conflictos que requieren resolucion manual")
    if report.summary["integrity_score"] == 100:
        print("  [OK] Todos los recursos criticos estan presentes")
    print()
    print("Archivos generados:")
    print("  - dev-resources-state.json")
    print("  - DEV-VALIDATION-REPORT.md")


if __name__ == "__main__":
    main()

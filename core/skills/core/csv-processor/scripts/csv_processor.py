#!/usr/bin/env python3
"""
CSV Processor - Script principal de procesamiento de archivos CSV.

Uso:
    python csv_processor.py input.csv output.csv --mode MODE [opciones]

Modos:
    clean      - Limpieza de datos (duplicados, nulos, formatos)
    transform  - Transformaciones (filtros, columnas, agregaciones)
    analyze    - Análisis estadístico y profiling
    convert    - Conversión de formato (CSV a otros)

Ejemplos:
    python csv_processor.py data.csv clean.csv --mode clean --remove-duplicates
    python csv_processor.py data.csv filtered.csv --mode transform --filter "age>=18"
    python csv_processor.py data.csv stats.json --mode analyze --stats all
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("[ERROR] Se requiere pandas. Instalar con: pip install pandas numpy")
    sys.exit(1)


def read_csv_safe(
    filepath: str, encoding: str = "utf-8", sep: str = None
) -> pd.DataFrame:
    """Lee CSV con manejo de errores y detección automática de separador."""
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

    # Detectar separador si no se especificó
    if sep is None:
        with open(filepath, "r", encoding=encoding, errors="replace") as f:
            first_line = f.readline()
            if "\t" in first_line:
                sep = "\t"
            elif ";" in first_line:
                sep = ";"
            else:
                sep = ","

    try:
        df = pd.read_csv(filepath, encoding=encoding, sep=sep, low_memory=False)
        return df
    except Exception as e:
        raise Exception(f"Error leyendo CSV: {e}")


def clean_data(df: pd.DataFrame, args) -> pd.DataFrame:
    """Operaciones de limpieza de datos."""

    # Eliminar duplicados
    if args.remove_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        print(f"[INFO] Eliminados {before - after} duplicados")

    # Manejar valores nulos
    if args.handle_nulls == "drop":
        before = len(df)
        df = df.dropna()
        after = len(df)
        print(f"[INFO] Eliminadas {before - after} filas con nulos")
    elif args.handle_nulls == "fill":
        # Rellenar numéricos con 0, strings con vacío
        for col in df.columns:
            if df[col].dtype in ["int64", "float64"]:
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna("")
        print("[INFO] Nulos rellenados con valores por defecto")

    # Normalizar espacios en blanco (strings)
    if args.normalize_whitespace:
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
        print("[INFO] Espacios normalizados")

    # Eliminar columnas completamente vacías
    if args.drop_empty_cols:
        empty_cols = df.columns[df.isnull().all()].tolist()
        if empty_cols:
            df = df.drop(columns=empty_cols)
            print(f"[INFO] Eliminadas columnas vacías: {empty_cols}")

    return df


def transform_data(df: pd.DataFrame, args) -> pd.DataFrame:
    """Operaciones de transformación."""

    # Filtrar filas
    if args.filter_query:
        try:
            before = len(df)
            df = df.query(args.filter_query)
            after = len(df)
            print(f"[INFO] Filtrado: {before} -> {after} filas")
        except Exception as e:
            print(f"[ERROR] Error en filtro: {e}")
            sys.exit(1)

    # Seleccionar columnas específicas
    if args.select_columns:
        cols = [c.strip() for c in args.select_columns.split(",")]
        existing_cols = [c for c in cols if c in df.columns]
        missing_cols = [c for c in cols if c not in df.columns]

        if missing_cols:
            print(f"[WARN] Columnas no encontradas: {missing_cols}")

        if existing_cols:
            df = df[existing_cols]
            print(f"[INFO] Seleccionadas {len(existing_cols)} columnas")

    # Renombrar columnas
    if args.rename:
        # Formato: "old1=new1,old2=new2"
        rename_dict = {}
        for pair in args.rename.split(","):
            if "=" in pair:
                old, new = pair.split("=", 1)
                rename_dict[old.strip()] = new.strip()

        if rename_dict:
            df = df.rename(columns=rename_dict)
            print(f"[INFO] Renombradas columnas: {list(rename_dict.keys())}")

    # Ordenar por columna
    if args.sort_by:
        if args.sort_by in df.columns:
            ascending = not args.descending
            df = df.sort_values(by=args.sort_by, ascending=ascending)
            print(f"[INFO] Ordenado por '{args.sort_by}'")
        else:
            print(f"[WARN] Columna de orden '{args.sort_by}' no existe")

    return df


def analyze_data(df: pd.DataFrame, args) -> dict:
    """Análisis estadístico del dataset."""

    stats = {
        "metadata": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
        },
        "column_stats": {},
    }

    for col in df.columns:
        col_stats = {
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_percent": round(df[col].isnull().sum() / len(df) * 100, 2),
            "unique_count": int(df[col].nunique()),
        }

        # Estadísticas para columnas numéricas
        if df[col].dtype in ["int64", "float64"]:
            col_stats.update(
                {
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean())
                    if not pd.isna(df[col].mean())
                    else None,
                    "median": float(df[col].median())
                    if not pd.isna(df[col].median())
                    else None,
                    "std": float(df[col].std()) if not pd.isna(df[col].std()) else None,
                }
            )

        stats["column_stats"][col] = col_stats

    return stats


def save_output(df_or_stats, output_path: str, mode: str, args):
    """Guarda el resultado en el formato apropiado."""

    path = Path(output_path)

    if mode == "analyze":
        # Guardar análisis como JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(df_or_stats, f, indent=2, ensure_ascii=False)
        print(f"[OK] Análisis guardado en: {output_path}")
    else:
        # Guardar DataFrame
        if path.suffix.lower() == ".json":
            df_or_stats.to_json(
                output_path, orient="records", indent=2, force_ascii=False
            )
        elif path.suffix.lower() in [".xlsx", ".xls"]:
            df_or_stats.to_excel(output_path, index=False)
            print(f"[TIP] Usar @xlsx para formateo avanzado de Excel")
        else:
            # Default: CSV
            sep = "\t" if path.suffix.lower() == ".tsv" else ","
            df_or_stats.to_csv(output_path, index=False, encoding="utf-8", sep=sep)

        print(f"[OK] Resultado guardado: {output_path}")
        print(f"[INFO] Filas: {len(df_or_stats)}, Columnas: {len(df_or_stats.columns)}")


def main():
    parser = argparse.ArgumentParser(
        description="Procesa archivos CSV para limpieza, transformación y análisis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Limpieza
  python csv_processor.py input.csv clean.csv --mode clean --remove-duplicates
  
  # Transformación
  python csv_processor.py input.csv output.csv --mode transform --filter "edad>=18"
  
  # Análisis
  python csv_processor.py input.csv stats.json --mode analyze
  
  # Conversión a Excel (integración con @xlsx)
  python csv_processor.py input.csv output.xlsx --mode clean
        """,
    )

    parser.add_argument("input", help="Archivo CSV de entrada")
    parser.add_argument("output", help="Archivo de salida")
    parser.add_argument(
        "--mode",
        choices=["clean", "transform", "analyze", "convert"],
        default="clean",
        help="Modo de operación",
    )
    parser.add_argument("--encoding", default="utf-8", help="Codificación del archivo")
    parser.add_argument(
        "--sep", default=None, help="Separador (auto-detectado por defecto)"
    )

    # Opciones de limpieza
    parser.add_argument(
        "--remove-duplicates", action="store_true", help="Eliminar filas duplicadas"
    )
    parser.add_argument(
        "--handle-nulls",
        choices=["drop", "fill", "ignore"],
        default="ignore",
        help="Cómo manejar valores nulos",
    )
    parser.add_argument(
        "--normalize-whitespace",
        action="store_true",
        help="Eliminar espacios extra en strings",
    )
    parser.add_argument(
        "--drop-empty-cols",
        action="store_true",
        help="Eliminar columnas completamente vacías",
    )

    # Opciones de transformación
    parser.add_argument("--filter-query", help="Filtro de filas (sintaxis pandas)")
    parser.add_argument(
        "--select-columns", help="Columnas a seleccionar (coma-separadas)"
    )
    parser.add_argument(
        "--rename", help="Renombrar columnas (formato: old=new,old2=new2)"
    )
    parser.add_argument("--sort-by", help="Columna para ordenar")
    parser.add_argument("--descending", action="store_true", help="Orden descendente")

    # Opciones de análisis
    parser.add_argument(
        "--stats",
        choices=["basic", "all"],
        default="basic",
        help="Nivel de estadísticas",
    )

    args = parser.parse_args()

    print(f"\n[CSV-PROCESSOR] Modo: {args.mode.upper()}")
    print(f"[INPUT] {args.input}")
    print(f"[OUTPUT] {args.output}")
    print("-" * 60)

    # Leer datos
    try:
        df = read_csv_safe(args.input, encoding=args.encoding, sep=args.sep)
        print(f"[INFO] Cargadas {len(df)} filas x {len(df.columns)} columnas")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # Procesar según modo
    if args.mode == "clean":
        df = clean_data(df, args)
        save_output(df, args.output, args.mode, args)

    elif args.mode == "transform":
        df = transform_data(df, args)
        save_output(df, args.output, args.mode, args)

    elif args.mode == "analyze":
        stats = analyze_data(df, args)
        save_output(stats, args.output, args.mode, args)

    elif args.mode == "convert":
        save_output(df, args.output, args.mode, args)

    print("\n[DONE] Procesamiento completado")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ETL Processor - Core Skill
Manipulación de datos ligera y sin fricción.
"""

import csv
import json
import argparse
import sys
import os
from pathlib import Path

# Intentar importar librerías opcionales
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

def csv_to_json(input_path, output_path):
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Convertido {input_path} -> {output_path} ({len(data)} registros)")

def json_to_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list) or not data:
        print("[ERROR] El JSON debe ser una lista de objetos.")
        return

    headers = data[0].keys()
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    print(f"[OK] Convertido {input_path} -> {output_path} ({len(data)} registros)")

def merge_csvs(input_dir, output_path):
    input_path = Path(input_dir)
    if not input_path.is_dir():
        print(f"[ERROR] {input_dir} no es un directorio.")
        return

    all_files = list(input_path.glob("*.csv"))
    if not all_files:
        print("[WARN] No se encontraron archivos CSV.")
        return

    print(f"[INFO] Unificando {len(all_files)} archivos...")
    
    # Leer header del primero
    with open(all_files[0], 'r', encoding='utf-8') as f:
        header = f.readline()

    with open(output_path, 'w', encoding='utf-8') as fout:
        fout.write(header)
        for fname in all_files:
            with open(fname, 'r', encoding='utf-8') as fin:
                # Saltar header de los siguientes
                # Nota: Esto asume estructura idéntica. Para algo robusto usaríamos pandas si existe.
                next(fin) 
                for line in fin:
                    fout.write(line)
    
    print(f"[OK] Unificado en {output_path}")

def filter_data(input_path, output_path, column, value):
    # Detección simple para CSV vs JSON
    is_json = str(input_path).endswith('.json')
    
    filtered = []
    count = 0
    
    if is_json:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for row in data:
                # Comparación string laxa
                if str(row.get(column)) == str(value):
                    filtered.append(row)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, indent=2)
            
    else: # Assume CSV
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            with open(output_path, 'w', encoding='utf-8', newline='') as fout:
                writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
                writer.writeheader()
                for row in reader:
                    if str(row.get(column)) == str(value):
                        writer.writerow(row)
                        count += 1
    
    print(f"[OK] Filtrado {count} registros donde {column}={value}")

def main():
    parser = argparse.ArgumentParser(description="ETL Data Processor")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # csv2json
    p_c2j = subparsers.add_parser('csv2json')
    p_c2j.add_argument('--input', required=True)
    p_c2j.add_argument('--output', required=True)

    # json2csv
    p_j2c = subparsers.add_parser('json2csv')
    p_j2c.add_argument('--input', required=True)
    p_j2c.add_argument('--output', required=True)

    # merge
    p_merge = subparsers.add_parser('merge')
    p_merge.add_argument('--input', required=True, help="Directory with CSVs")
    p_merge.add_argument('--output', required=True)

    # filter
    p_filter = subparsers.add_parser('filter')
    p_filter.add_argument('--input', required=True)
    p_filter.add_argument('--output', default="filtered_output.csv")
    p_filter.add_argument('--column', required=True)
    p_filter.add_argument('--value', required=True)

    args = parser.parse_args()

    try:
        if args.command == 'csv2json':
            csv_to_json(args.input, args.output)
        elif args.command == 'json2csv':
            json_to_csv(args.input, args.output)
        elif args.command == 'merge':
            merge_csvs(args.input, args.output)
        elif args.command == 'filter':
            filter_data(args.input, args.output, args.column, args.value)
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
01_explorar_eda.py - Análisis Exploratorio de Datos (EDA)
Carga el CSV de fallecidos por COVID-19, limpia los datos, genera estadísticas generales
y exporta datos agregados para visualización y pronóstico.
"""

import os
import pandas as pd
import numpy as np

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "fallecidos_covid.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def cargar_y_limpiar_datos(filepath):
    print(f"Cargando dataset desde: {filepath}...")
    # Cargar CSV delimitado por punto y coma
    df = pd.read_csv(filepath, sep=";", dtype={"UBIGEO": str, "UUID": str})

    # Convertir FECHA_FALLECIMIENTO a datetime (formato YYYYMMDD)
    df["FECHA_FALLECIMIENTO"] = pd.to_datetime(
        df["FECHA_FALLECIMIENTO"].astype(str), format="%Y%m%d", errors="coerce"
    )

    # Convertir FECHA_CORTE a datetime
    if "FECHA_CORTE" in df.columns:
        df["FECHA_CORTE"] = pd.to_datetime(
            df["FECHA_CORTE"].astype(str), format="%Y%m%d", errors="coerce"
        )

    # Convertir EDAD_DECLARADA a entero
    df["EDAD_DECLARADA"] = pd.to_numeric(df["EDAD_DECLARADA"], errors="coerce")

    # Eliminar registros con fecha de fallecimiento nula
    registros_iniciales = len(df)
    df = df.dropna(subset=["FECHA_FALLECIMIENTO"]).copy()
    print(f"Registros procesados: {len(df)} / {registros_iniciales}")

    # Clasificación por Grupo Etario
    bins = [0, 18, 40, 60, 80, 120]
    labels = ["0-17 años", "18-39 años", "40-59 años", "60-79 años", "80+ años"]
    df["GRUPO_ETARIO"] = pd.cut(df["EDAD_DECLARADA"], bins=bins, labels=labels, right=False)

    return df


def generar_estadisticas(df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n--- RESUMEN GENERAL ---")
    total_fallecidos = len(df)
    min_fecha = df["FECHA_FALLECIMIENTO"].min().strftime("%Y-%m-%d")
    max_fecha = df["FECHA_FALLECIMIENTO"].max().strftime("%Y-%m-%d")
    promedio_edad = df["EDAD_DECLARADA"].mean()
    mediana_edad = df["EDAD_DECLARADA"].median()

    print(f"Total de fallecidos: {total_fallecidos:,}")
    print(f"Rango de fechas: {min_fecha} hasta {max_fecha}")
    print(f"Promedio de edad: {promedio_edad:.1f} años (Mediana: {mediana_edad:.0f} años)")

    # Distribución por Sexo
    print("\n--- DISTRIBUCIÓN POR SEXO ---")
    sexo_df = df["SEXO"].value_counts().reset_index()
    sexo_df.columns = ["SEXO", "CANTIDAD"]
    sexo_df["PORCENTAJE"] = (sexo_df["CANTIDAD"] / total_fallecidos * 100).round(2)
    print(sexo_df.to_string(index=False))

    # Distribución por Departamento
    print("\n--- TOP 10 DEPARTAMENTOS ---")
    dep_df = df["DEPARTAMENTO"].value_counts().reset_index()
    dep_df.columns = ["DEPARTAMENTO", "CANTIDAD"]
    print(dep_df.head(10).to_string(index=False))

    # Serie temporal diaria
    diario_df = (
        df.groupby("FECHA_FALLECIMIENTO")
        .size()
        .reset_index(name="FALLECIDOS")
        .sort_values("FECHA_FALLECIMIENTO")
    )
    diario_df.to_csv(os.path.join(OUTPUT_DIR, "fallecidos_diario.csv"), index=False)

    # Serie temporal mensual
    df["ANIO_MES"] = df["FECHA_FALLECIMIENTO"].dt.to_period("M").astype(str)
    mensual_df = (
        df.groupby("ANIO_MES")
        .size()
        .reset_index(name="FALLECIDOS")
        .sort_values("ANIO_MES")
    )
    mensual_df.to_csv(os.path.join(OUTPUT_DIR, "fallecidos_mensual.csv"), index=False)

    print(f"\nResultados agregados guardados en la carpeta: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        print(f"Error: No se encontró el archivo {DATA_PATH}")
    else:
        df = cargar_y_limpiar_datos(DATA_PATH)
        generar_estadisticas(df)

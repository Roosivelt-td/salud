#!/usr/bin/env python3
"""
02_pronostico_cli.py - Script de Pronóstico de Series Temporales (Forecasting)
Aplica modelos de Prophet y Statsmodels (Holt-Winters) para proyectar
tendencias futuras de mortalidad por COVID-19 con bandas de confianza.
"""

import os
import pandas as pd
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "fallecidos_covid.csv")


def cargar_datos_agregados(frecuencia="D"):
    """
    Carga el CSV original y agrupa por fecha según la frecuencia solicitada:
    'D' = Diario, 'W' = Semanal, 'M' = Mensual
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"No existe el archivo {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, sep=";", usecols=["FECHA_FALLECIMIENTO"])
    df["FECHA"] = pd.to_datetime(
        df["FECHA_FALLECIMIENTO"].astype(str), format="%Y%m%d", errors="coerce"
    )
    df = df.dropna(subset=["FECHA"]).copy()

    # Agrupar por frecuencia
    df_agg = (
        df.groupby(pd.Grouper(key="FECHA", freq=frecuencia))
        .size()
        .reset_index(name="y")
        .rename(columns={"FECHA": "ds"})
    )
    return df_agg


def pronosticar_con_prophet(df_agg, periodos=30, freq="D"):
    """
    Pronóstico utilizando la librería Facebook Prophet.
    """
    try:
        from prophet import Prophet

        print(f"Entrenando modelo Prophet (Frecuencia: {freq}, Periodos a futuro: {periodos})...")
        modelo = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=(freq == "D"),
            daily_seasonality=False,
            interval_width=0.95,  # 95% intervalo de confianza
        )
        modelo.fit(df_agg)

        futuro = modelo.make_future_dataframe(periods=periodos, freq=freq)
        pronostico = modelo.predict(futuro)

        # Truncar valores negativos a cero (los fallecidos no pueden ser negativos)
        pronostico["yhat"] = pronostico["yhat"].clip(lower=0)
        pronostico["yhat_lower"] = pronostico["yhat_lower"].clip(lower=0)
        pronostico["yhat_upper"] = pronostico["yhat_upper"].clip(lower=0)

        return modelo, pronostico

    except ImportError:
        print("Prophet no está instalado. Usando fallback con Statsmodels (Exponential Smoothing)...")
        return None, pronosticar_con_statsmodels(df_agg, periodos=periodos, freq=freq)


def pronosticar_con_statsmodels(df_agg, periodos=30, freq="D"):
    """
    Modelo de Suavizamiento Exponencial / Holt-Winters como alternativa robusta.
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    df = df_agg.copy().set_index("ds")
    df = df.asfreq(freq).fillna(0)

    print("Entrenando modelo Holt-Winters (Exponential Smoothing)...")
    model = ExponentialSmoothing(
        df["y"],
        trend="add",
        seasonal="add" if len(df) > 24 else None,
        seasonal_periods=12 if freq == "M" else 7,
    ).fit()

    pred = model.forecast(periodos)

    # Crear dataframe estructurado similar a Prophet
    future_dates = pd.date_range(start=df.index[-1], periods=periodos + 1, freq=freq)[1:]

    # Estimación simple de bandas de confianza basadas en la desviación estándar de los residuos
    residual_std = model.resid.std()

    forecast_df = pd.DataFrame({
        "ds": future_dates,
        "yhat": pred.values.clip(min=0),
        "yhat_lower": (pred.values - 1.96 * residual_std).clip(min=0),
        "yhat_upper": (pred.values + 1.96 * residual_std).clip(min=0),
    })

    return forecast_df


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Pronóstico Mensual (12 meses a futuro)
    df_mensual = cargar_datos_agregados(frecuencia="MS")
    modelo_m, p_mensual = pronosticar_con_prophet(df_mensual, periodos=12, freq="MS")

    output_csv = os.path.join(OUTPUT_DIR, "pronostico_mensual.csv")
    if isinstance(p_mensual, pd.DataFrame):
        p_mensual[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_csv(output_csv, index=False)
    else:
        p_mensual[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_csv(output_csv, index=False)

    print(f"Pronóstico guardado exitosamente en: {output_csv}")

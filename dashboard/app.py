import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración de página de Streamlit
st.set_page_config(
    page_title="COVID-19 Perú - Analytics & Forecasting Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "fallecidos_covid.csv")

# CSS personalizado para estilo moderno similar a Power BI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background-color: #F3F4F6;
        border-left: 5px solid #2563EB;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .kpi-title {
        font-size: 0.85rem;
        color: #6B7280;
        text-transform: uppercase;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1F2937;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def cargar_datos(path):
    if not os.path.exists(path):
        return None

    df = pd.read_csv(
        path,
        sep=";",
        dtype={"UBIGEO": str, "UUID": str},
        usecols=[
            "FECHA_CORTE", "FECHA_FALLECIMIENTO", "EDAD_DECLARADA",
            "SEXO", "CLASIFICACION_DEF", "DEPARTAMENTO", "PROVINCIA", "DISTRITO"
        ]
    )

    # Convertir fechas
    df["FECHA_FALLECIMIENTO"] = pd.to_datetime(
        df["FECHA_FALLECIMIENTO"].astype(str), format="%Y%m%d", errors="coerce"
    )
    df["FECHA_CORTE"] = pd.to_datetime(
        df["FECHA_CORTE"].astype(str), format="%Y%m%d", errors="coerce"
    )

    # Convertir EDAD
    df["EDAD_DECLARADA"] = pd.to_numeric(df["EDAD_DECLARADA"], errors="coerce")

    # Eliminar nulos en fecha principal
    df = df.dropna(subset=["FECHA_FALLECIMIENTO"]).copy()

    # Grupos Etarios
    bins = [0, 18, 40, 60, 80, 120]
    labels = ["0-17 años", "18-39 años", "40-59 años", "60-79 años", "80+ años"]
    df["GRUPO_ETARIO"] = pd.cut(df["EDAD_DECLARADA"], bins=bins, labels=labels, right=False)

    return df


# Carga de datos
df_raw = cargar_datos(DATA_PATH)

if df_raw is None:
    st.error(f"❌ No se pudo encontrar el archivo de datos en: `{DATA_PATH}`")
    st.stop()

# --- BARRA LATERAL (FILTROS EN TIEMPO REAL) ---
st.sidebar.image("https://img.icons8.com/color/96/000000/bar-chart.png", width=60)
st.sidebar.title("🎛️ Filtros de Análisis")

# 1. Filtro de Rango de Fechas
min_date = df_raw["FECHA_FALLECIMIENTO"].min().date()
max_date = df_raw["FECHA_FALLECIMIENTO"].max().date()

start_date, end_date = st.sidebar.date_input(
    "Rango de Fechas",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# 2. Filtro de Departamento
deps_disponibles = sorted(df_raw["DEPARTAMENTO"].dropna().unique().tolist())
deps_seleccionados = st.sidebar.multiselect(
    "Departamento(s)",
    options=deps_disponibles,
    default=[]
)

# 3. Filtro de Sexo
sexos_disponibles = sorted(df_raw["SEXO"].dropna().unique().tolist())
sexo_seleccionado = st.sidebar.multiselect(
    "Sexo",
    options=sexos_disponibles,
    default=sexos_disponibles
)

# 4. Filtro de Clasificación
clasif_disponibles = sorted(df_raw["CLASIFICACION_DEF"].dropna().unique().tolist())
clasif_seleccionada = st.sidebar.multiselect(
    "Criterio de Clasificación",
    options=clasif_disponibles,
    default=clasif_disponibles
)

# 5. Filtro de Rango de Edad
min_edad = int(df_raw["EDAD_DECLARADA"].min())
max_edad = int(df_raw["EDAD_DECLARADA"].max())
rango_edad = st.sidebar.slider(
    "Rango de Edad",
    min_value=min_edad,
    max_value=max_edad,
    value=(min_edad, max_edad)
)

# --- APLICAR FILTROS EN DATAFRAME ---
mask = (
    (df_raw["FECHA_FALLECIMIENTO"].dt.date >= start_date) &
    (df_raw["FECHA_FALLECIMIENTO"].dt.date <= end_date) &
    (df_raw["SEXO"].isin(sexo_seleccionado)) &
    (df_raw["CLASIFICACION_DEF"].isin(clasif_seleccionada)) &
    (df_raw["EDAD_DECLARADA"].between(rango_edad[0], rango_edad[1]))
)

if deps_seleccionados:
    mask = mask & (df_raw["DEPARTAMENTO"].isin(deps_seleccionados))

df_filtrado = df_raw[mask].copy()

# --- ENCABEZADO ---
st.markdown('<div class="main-header">📊 Dashboard de Análisis y Pronóstico - COVID-19 Perú</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Plataforma interactiva estilo Power BI en Linux con Python, Streamlit y Prophet</div>', unsafe_allow_html=True)

# Banner interactivo hacia el Simulador Epidemiológico
st.info("💡 **¿Deseas simular la aparición de un NUEVO virus a 5 años (2025-2029)?** Utiliza la nueva página de simulación epidemiológica SEIR en la barra lateral o mediante el enlace direct: **[Simulador Futuro 5 Años](http://localhost:8501/Simulador_Futuro)**.")

# --- TABS DE LA APLICACIÓN ---
tab_resumen, tab_geo, tab_forecast, tab_tabla = st.tabs([
    "📈 Resumen & KPIs",
    "🗺️ Demografía & Geografía",
    "🔮 Pronóstico Futuro (Prophet)",
    "📁 Explorador de Datos"
])

# ==============================================================================
# TAB 1: RESUMEN & KPIS
# ==============================================================================
with tab_resumen:
    # FILA DE KPIS
    c1, c2, c3, c4, c5 = st.columns(5)

    total_casos = len(df_filtrado)
    promedio_edad = df_filtrado["EDAD_DECLARADA"].mean() if total_casos > 0 else 0
    pct_hombres = (df_filtrado["SEXO"] == "MASCULINO").mean() * 100 if total_casos > 0 else 0

    # Pico máximo diario
    if total_casos > 0:
        daily_counts = df_filtrado.groupby("FECHA_FALLECIMIENTO").size()
        pico_max = daily_counts.max()
        fecha_pico = daily_counts.idxmax().strftime("%d/%m/%Y")
    else:
        pico_max, fecha_pico = 0, "N/A"

    c1.metric("Total Fallecidos", f"{total_casos:,}")
    c2.metric("Promedio de Edad", f"{promedio_edad:.1f} años")
    c3.metric("% Hombres", f"{pct_hombres:.1f}%")
    c4.metric("Pico Máximo Diario", f"{pico_max:,}")
    c5.metric("Fecha Pico Máximo", fecha_pico)

    st.markdown("---")

    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("📈 Tendencia Temporal de Fallecidos")
        if total_casos > 0:
            ts_daily = (
                df_filtrado.groupby("FECHA_FALLECIMIENTO")
                .size()
                .reset_index(name="FALLECIDOS")
                .sort_values("FECHA_FALLECIMIENTO")
            )
            # Promedio móvil 7 días
            ts_daily["MEDIA_MOVIL_7D"] = ts_daily["FALLECIDOS"].rolling(7, min_periods=1).mean()

            fig_ts = go.Figure()
            fig_ts.add_trace(go.Bar(
                x=ts_daily["FECHA_FALLECIMIENTO"],
                y=ts_daily["FALLECIDOS"],
                name="Fallecidos Diarios",
                marker_color="#93C5FD",
                opacity=0.6
            ))
            fig_ts.add_trace(go.Scatter(
                x=ts_daily["FECHA_FALLECIMIENTO"],
                y=ts_daily["MEDIA_MOVIL_7D"],
                name="Promedio Móvil (7 días)",
                line=dict(color="#1E40AF", width=3)
            ))
            fig_ts.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=380,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="Fecha",
                yaxis_title="Cantidad de Fallecidos"
            )
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")

    with col_der:
        st.subheader("🔬 Criterios de Clasificación")
        if total_casos > 0:
            crit_df = df_filtrado["CLASIFICACION_DEF"].value_counts().reset_index()
            crit_df.columns = ["CRITERIO", "CANTIDAD"]

            fig_pie = px.pie(
                crit_df,
                names="CRITERIO",
                values="CANTIDAD",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=380)
            st.plotly_chart(fig_pie, use_container_width=True)


# ==============================================================================
# TAB 2: DEMOGRAFÍA & GEOGRAFÍA
# ==============================================================================
with tab_geo:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("🏙️ Top Departamentos más Afectados")
        if len(df_filtrado) > 0:
            top_deps = df_filtrado["DEPARTAMENTO"].value_counts().head(12).reset_index()
            top_deps.columns = ["DEPARTAMENTO", "FALLECIDOS"]

            fig_dep = px.bar(
                top_deps.sort_values("FALLECIDOS", ascending=True),
                x="FALLECIDOS",
                y="DEPARTAMENTO",
                orientation="h",
                color="FALLECIDOS",
                color_continuous_scale="Reds"
            )
            fig_dep.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_dep, use_container_width=True)

    with col_g2:
        st.subheader("👥 Distribución por Grupo Etario y Sexo")
        if len(df_filtrado) > 0:
            etario_sexo = df_filtrado.groupby(["GRUPO_ETARIO", "SEXO"], observed=False).size().reset_index(name="FALLECIDOS")

            fig_age = px.bar(
                etario_sexo,
                x="GRUPO_ETARIO",
                y="FALLECIDOS",
                color="SEXO",
                barmode="group",
                color_discrete_map={"MASCULINO": "#2563EB", "FEMENINO": "#EC4899"}
            )
            fig_age.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10), xaxis_title="Grupo Etario")
            st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")
    st.subheader("🗓️ Matriz de Calor: Fallecidos por Año y Mes")
    if len(df_filtrado) > 0:
        df_heatmap = df_filtrado.copy()
        df_heatmap["AÑO"] = df_heatmap["FECHA_FALLECIMIENTO"].dt.year
        df_heatmap["MES_NUM"] = df_heatmap["FECHA_FALLECIMIENTO"].dt.month
        df_heatmap["MES"] = df_heatmap["FECHA_FALLECIMIENTO"].dt.strftime("%b")

        pivot_heat = df_heatmap.pivot_table(
            index="AÑO",
            columns="MES_NUM",
            values="EDAD_DECLARADA",
            aggfunc="count",
            fill_value=0
        )
        meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        pivot_heat.columns = [meses_nombres[i-1] for i in pivot_heat.columns]

        fig_heat = px.imshow(
            pivot_heat,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="OrRd",
            labels=dict(x="Mes", y="Año", color="Fallecidos")
        )
        fig_heat.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_heat, use_container_width=True)


# ==============================================================================
# TAB 3: PRONÓSTICO FUTURO (PROPHET)
# ==============================================================================
with tab_forecast:
    st.subheader("🔮 Modelo Predictivo de Tendencias (Forecasting)")
    st.write("Genera proyecciones hacia el futuro utilizando algoritmos de series temporales (Prophet / Holt-Winters) con intervalos de confianza.")

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)

    with col_ctrl1:
        frecuencia_sel = st.selectbox(
            "Frecuencia de Agrupación",
            options=["Mensual (Recomendado)", "Semanal", "Diario"]
        )

    freq_code = "MS" if "Mensual" in frecuencia_sel else ("W" if "Semanal" in frecuencia_sel else "D")

    with col_ctrl2:
        periodos_futuro = st.slider(
            "Periodos a Pronosticar hacia el Futuro",
            min_value=1,
            max_value=36 if freq_code != "D" else 180,
            value=12 if freq_code != "D" else 60
        )

    with col_ctrl3:
        confiabilidad = st.selectbox(
            "Intervalo de Confianza",
            options=["95%", "90%", "80%"],
            index=0
        )

    conf_val = float(confiabilidad.replace("%", "")) / 100.0

    if st.button("🚀 Ejecutar Pronóstico Predictivo", type="primary"):
        with st.spinner("Procesando datos y entrenando modelo de serie temporal..."):
            # Preparar dataset agregado
            df_prophet_input = (
                df_filtrado.groupby(pd.Grouper(key="FECHA_FALLECIMIENTO", freq=freq_code))
                .size()
                .reset_index(name="y")
                .rename(columns={"FECHA_FALLECIMIENTO": "ds"})
            )

            if len(df_prophet_input) < 5:
                st.error("Insuficientes datos en el rango seleccionado para generar un pronóstico fiable.")
            else:
                try:
                    from prophet import Prophet

                    m = Prophet(
                        yearly_seasonality=True,
                        weekly_seasonality=(freq_code == "D"),
                        daily_seasonality=False,
                        interval_width=conf_val
                    )
                    m.fit(df_prophet_input)

                    futuro = m.make_future_dataframe(periods=periodos_futuro, freq=freq_code)
                    forecast = m.predict(futuro)

                    # Truncar valores negativos
                    forecast["yhat"] = forecast["yhat"].clip(lower=0)
                    forecast["yhat_lower"] = forecast["yhat_lower"].clip(lower=0)
                    forecast["yhat_upper"] = forecast["yhat_upper"].clip(lower=0)

                    # Graficar con Plotly
                    fig_fc = go.Figure()

                    # Datos Históricos
                    fig_fc.add_trace(go.Scatter(
                        x=df_prophet_input["ds"],
                        y=df_prophet_input["y"],
                        mode="lines+markers",
                        name="Datos Históricos Reales",
                        line=dict(color="#2563EB", width=2),
                        marker=dict(size=4)
                    ))

                    # Banda de confianza
                    fig_fc.add_trace(go.Scatter(
                        x=forecast["ds"].tolist() + forecast["ds"].tolist()[::-1],
                        y=forecast["yhat_upper"].tolist() + forecast["yhat_lower"].tolist()[::-1],
                        fill="toself",
                        fillcolor="rgba(147, 197, 253, 0.3)",
                        line=dict(color="rgba(255,255,255,0)"),
                        hoverinfo="skip",
                        name=f"Banda de Confianza ({confiabilidad})"
                    ))

                    # Tendencia Pronosticada
                    fig_fc.add_trace(go.Scatter(
                        x=forecast["ds"],
                        y=forecast["yhat"],
                        mode="lines",
                        name="Pronóstico (Tendencia)",
                        line=dict(color="#DC2626", width=3, dash="dash")
                    ))

                    fig_fc.update_layout(
                        title=f"Proyección a {periodos_futuro} periodos futuros ({frecuencia_sel})",
                        xaxis_title="Fecha",
                        yaxis_title="Fallecidos Proyectados",
                        height=480,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )

                    st.plotly_chart(fig_fc, use_container_width=True)

                    # Mostrar Tabla de Predicciones Futuras
                    st.subheader("📋 Tabla de Predicciones Futuras")
                    df_future_only = forecast[forecast["ds"] > df_prophet_input["ds"].max()][
                        ["ds", "yhat", "yhat_lower", "yhat_upper"]
                    ].copy()

                    df_future_only.columns = ["Fecha", "Estimación Esperada", "Límite Inferior", "Límite Superior"]
                    df_future_only["Estimación Esperada"] = df_future_only["Estimación Esperada"].round(0)
                    df_future_only["Límite Inferior"] = df_future_only["Límite Inferior"].round(0)
                    df_future_only["Límite Superior"] = df_future_only["Límite Superior"].round(0)

                    st.dataframe(df_future_only, use_container_width=True)

                    # Botón de Descarga
                    csv_export = df_future_only.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar Predicciones (CSV)",
                        data=csv_export,
                        file_name="predicciones_covid_peru.csv",
                        mime="text/csv"
                    )

                except Exception as e:
                    st.error(f"Error al ejecutar el modelo: {e}")


# ==============================================================================
# TAB 4: EXPLORADOR DE DATOS
# ==============================================================================
with tab_tabla:
    st.subheader("📁 Explorador Interactivo de Registros")
    st.write(f"Mostrando **{len(df_filtrado):,}** registros filtrados del total original (**{len(df_raw):,}**).")

    # Mostrar dataframe interactivo
    st.dataframe(
        df_filtrado[[
            "FECHA_FALLECIMIENTO", "EDAD_DECLARADA", "SEXO",
            "CLASIFICACION_DEF", "DEPARTAMENTO", "PROVINCIA", "DISTRITO"
        ]].head(1000),
        use_container_width=True
    )

    st.caption("Nota: Se muestra una vista previa de los primeros 1,000 registros filtrados.")

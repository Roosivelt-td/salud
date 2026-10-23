import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy.integrate import odeint

# Configuración de la página
st.set_page_config(
    page_title="Simulador de Peligrosidad vs COVID-19",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS estilo Power BI
st.markdown("""
<style>
    .sim-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sim-sub {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background-color: #F8FAFC;
        border-top: 4px solid #2563EB;
        padding: 0.9rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .kpi-title {
        font-size: 0.8rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
    }
    .kpi-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
    }
    .comparison-banner {
        background-color: #EFF6FF;
        border-left: 5px solid #2563EB;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1.2rem;
        color: #1E40AF;
        font-size: 1.05rem;
    }
    .alert-banner {
        background-color: #FEF2F2;
        border-left: 5px solid #DC2626;
        padding: 0.9rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        color: #991B1B;
    }
    /* Estilos para las tarjetas de Top Departamentos */
    .dep-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }
    .dep-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 1rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 6px;
        border-bottom: 1px solid #334155;
        padding-bottom: 4px;
    }
    .dep-rank {
        background-color: #2563EB;
        color: #FFFFFF;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 10px;
    }
    .dep-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
    }
    .dep-metric-box {
        background-color: #0F172A;
        border-radius: 6px;
        padding: 5px 8px;
    }
    .dep-metric-label {
        font-size: 0.65rem;
        color: #94A3B8;
        text-transform: uppercase;
        font-weight: 600;
    }
    .dep-metric-val {
        font-size: 0.9rem;
        font-weight: 700;
    }
    .dep-red { color: #F87171; }
    .dep-blue { color: #60A5FA; }
    .dep-amber { color: #FBBF24; }
</style>
""", unsafe_allow_html=True)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "fallecidos_covid.csv")

# ------------------------------------------------------------------------------
# BASELINE HISTÓRICO REAL DE COVID-19 EN PERÚ (BASE = 100%)
# ------------------------------------------------------------------------------
COVID_BASE_FALLECIDOS = 220918    # Total real del CSV en Perú
COVID_BASE_INFECTADOS = 11800000  # Estimación de contagios totales en olas previas
COVID_BASE_PICO_DIARIO = 840     # Pico diario real de muertes en Perú (Abril 2021)
COVID_BASE_PICO_UCI = 3200       # Pico de demanda UCI en Perú

@st.cache_data(ttl=3600)
def obtener_pesos_historicos_peru(path):
    """
    Extrae la matriz de distribución real histórica por departamento, edad y sexo desde fallecidos_covid.csv.
    """
    if not os.path.exists(path):
        dep_weights = pd.Series({"LIMA": 0.441, "PIURA": 0.060, "LA LIBERTAD": 0.050, "CALLAO": 0.050, "AREQUIPA": 0.048})
        age_weights = pd.Series({"0-17 años": 0.005, "18-39 años": 0.045, "40-59 años": 0.200, "60-79 años": 0.480, "80+ años": 0.270})
        sex_weights = pd.Series({"MASCULINO": 0.63, "FEMENINO": 0.37})
        return dep_weights, age_weights, sex_weights

    df = pd.read_csv(
        path, sep=";",
        usecols=["DEPARTAMENTO", "EDAD_DECLARADA", "SEXO"],
        dtype={"DEPARTAMENTO": str, "SEXO": str}
    )
    df["EDAD_DECLARADA"] = pd.to_numeric(df["EDAD_DECLARADA"], errors="coerce")

    bins = [0, 18, 40, 60, 80, 120]
    labels = ["0-17 años", "18-39 años", "40-59 años", "60-79 años", "80+ años"]
    df["GRUPO_ETARIO"] = pd.cut(df["EDAD_DECLARADA"], bins=bins, labels=labels, right=False)

    dep_weights = df["DEPARTAMENTO"].value_counts(normalize=True)
    age_weights = df["GRUPO_ETARIO"].value_counts(normalize=True)
    sex_weights = df["SEXO"].value_counts(normalize=True)

    return dep_weights, age_weights, sex_weights

dep_weights, age_weights, sex_weights = obtener_pesos_historicos_peru(DATA_PATH)

# ------------------------------------------------------------------------------
# ENCABEZADO
# ------------------------------------------------------------------------------
st.markdown('<div class="sim-title">🔮 Simulador de Impacto de un Nuevo Virus (Relativo a COVID-19 = 100%)</div>', unsafe_allow_html=True)
st.markdown('<div class="sim-sub">Evalúa qué tan peligroso sería un nuevo virus comparado con la gravedad histórica del COVID-19 en el Perú.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# PANEL LATERAL DE CONFIGURACIÓN RELATIVA
# ------------------------------------------------------------------------------
st.sidebar.title("🎛️ Parámetros del Nuevo Virus")

# 1. Año y Fecha
st.sidebar.subheader("📅 Fecha de Aparición")
anio_brote = st.sidebar.selectbox("Año de Aparición del Nuevo Virus", options=[2025, 2026, 2027, 2028, 2029, 2030], index=2) # Default 2027

meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
mes_brote_nombre = st.sidebar.select_slider("Mes de Inicio", options=meses_nombres, value="Mayo")
mes_brote_idx = meses_nombres.index(mes_brote_nombre) + 1

# 2. ÍNDICES DE PELIGROSIDAD RELATIVOS A COVID-19 (100% = COVID)
st.sidebar.subheader("☣️ Peligrosidad Relativa (% vs COVID-19)")

pct_letalidad = st.sidebar.slider(
    "Poder de Fatalidad / Gravedad (% vs COVID)",
    min_value=10, max_value=300, value=100, step=5,
    help="100% = Misma gravedad que COVID-19. 75% = 25% menos fatal. 130% = 30% más mortal."
)

pct_contagio = st.sidebar.slider(
    "Velocidad de Contagio / Propagación (% vs COVID)",
    min_value=10, max_value=300, value=100, step=5,
    help="100% = Mismo ritmo de transmisión que COVID-19. 150% = Se propaga 50% más rápido."
)

# 3. Capacidad de Respuesta del Perú en ese Año
st.sidebar.subheader("🛡️ Preparación Sanitaria del Perú")
camas_uci_disp = st.sidebar.number_input("Capacidad de Camas UCI Disponibles", value=2800, step=100)
dias_retraso_cuarentena = st.sidebar.slider("Días de Retraso en Medidas de Contención", min_value=0, max_value=90, value=30)
efectividad_cuarentena = st.sidebar.slider("Efectividad de Medidas / Cuarentena (%)", min_value=0, max_value=90, value=50)

# ------------------------------------------------------------------------------
# MODELADO MATEMÁTICO BASADO EN EL ÍNDICE DE POTENCIA
# ------------------------------------------------------------------------------
# Crecimiento poblacional proyectado del Perú (~0.8% anual)
poblacion_peru = int(33000000 * ((1.008) ** (anio_brote - 2024)))

# Calibración dinámica del modelo SEIR ajustado por los porcentajes del usuario
factor_letalidad = pct_letalidad / 100.0
factor_contagio = pct_contagio / 100.0

r0_efectivo = 2.8 * factor_contagio
ifr_efectivo = 1.8 * factor_letalidad

duracion_dias = 10
incubacion_dias = 4

sigma = 1.0 / incubacion_dias
gamma = (1.0 - (ifr_efectivo / 100.0)) / duracion_dias
mu = (ifr_efectivo / 100.0) / duracion_dias

beta_init = r0_efectivo * (gamma + mu)
beta_mitig = beta_init * (1.0 - (efectividad_cuarentena / 100.0))

def beta_func(t):
    if t < dias_retraso_cuarentena:
        return beta_init
    else:
        return beta_mitig

# Simulación a 24 meses (730 días) comenzando exactamente en la fecha elegida
dias_sim = 730
t = np.linspace(0, dias_sim, dias_sim)

# Semilla inicial
I0 = int(20 * factor_contagio)
E0 = int(50 * factor_contagio)
S0 = poblacion_peru - I0 - E0
y0 = S0, E0, I0, 0, 0

def ecuacion_seir(y, t, N):
    S_t, E_t, I_t, R_t, D_t = y
    b = beta_func(t)
    dS = -b * S_t * I_t / N
    dE = b * S_t * I_t / N - sigma * E_t
    dI = sigma * E_t - gamma * I_t - mu * I_t
    dR = gamma * I_t
    dD = mu * I_t
    return dS, dE, dI, dR, dD

sol = odeint(ecuacion_seir, y0, t, args=(poblacion_peru,))
S_res, E_res, I_res, R_res, D_res = sol.T

fallecidos_diarios = np.diff(D_res, prepend=0)
demanda_uci_diaria = I_res * 0.045 * factor_letalidad

# Fechas dinámicas estrictas para el año seleccionado
fecha_inicio_brote = pd.Timestamp(year=anio_brote, month=mes_brote_idx, day=1)
fechas_sim = pd.date_range(start=fecha_inicio_brote, periods=dias_sim, freq="D")

df_sim = pd.DataFrame({
    "Fecha": fechas_sim,
    "Infectados_Activos": I_res,
    "Fallecidos_Diarios": fallecidos_diarios,
    "Fallecidos_Acumulados": D_res,
    "Demanda_UCI": demanda_uci_diaria
})

total_fallecidos_est = int(D_res[-1])
total_infectados_est = int(R_res[-1] + D_res[-1])
pico_fallecidos_diario = int(np.max(fallecidos_diarios))
pico_idx = np.argmax(fallecidos_diarios)
fecha_pico_str = fechas_sim[pico_idx].strftime("%d/%m/%Y")
pico_uci_est = int(np.max(demanda_uci_diaria))
dias_saturacion = int(np.sum(demanda_uci_diaria > camas_uci_disp))

# ------------------------------------------------------------------------------
# BANNER COMPARATIVO VS COVID-19 REAL
# ------------------------------------------------------------------------------
diferencia_fallecidos = total_fallecidos_est - COVID_BASE_FALLECIDOS
pct_dif_fallecidos = (diferencia_fallecidos / COVID_BASE_FALLECIDOS) * 100.0

if pct_dif_fallecidos > 0:
    comparacion_str = f"⚠️ Con un **{pct_letalidad}% de gravedad** y **{pct_contagio}% de contagio**, este nuevo virus en **{anio_brote}** sería **{abs(pct_dif_fallecidos):.1f}% MÁS FATAL** que la COVID-19 original (<b>+{diferencia_fallecidos:,} muertes adicionales</b>)."
elif pct_dif_fallecidos < 0:
    comparacion_str = f"✅ Con un **{pct_letalidad}% de gravedad** y **{pct_contagio}% de contagio**, este nuevo virus en **{anio_brote}** causaría **{abs(pct_dif_fallecidos):.1f}% MENOS muertes** que la COVID-19 original (<b>{abs(diferencia_fallecidos):,} muertes menos</b>)."
else:
    comparacion_str = f"➡️ Con un **100% de gravedad**, el impacto en **{anio_brote}** sería equivalente a la pandemia original de COVID-19 (<b>~220,918 fallecidos</b>)."

st.markdown(f'<div class="comparison-banner">{comparacion_str}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# KPIS PRINCIPALES
# ------------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(f"Fallecidos Proyectados ({anio_brote})", f"{total_fallecidos_est:,}", f"{pct_dif_fallecidos:+.1f}% vs COVID")
k2.metric(f"Infectados Totales ({anio_brote})", f"{total_infectados_est:,}")
k3.metric("Pico Diario Máximo", f"{pico_fallecidos_diario:,}", f"Fecha: {fecha_pico_str}")
k4.metric("Demanda Máxima UCI", f"{pico_uci_est:,} camas")
k5.metric("Días Saturación UCI", f"{dias_saturacion} días")

if dias_saturacion > 0:
    st.markdown(f"""
    <div class="alert-banner">
        🚨 <b>COLAPSO SANITARIO DETECTADO EN {anio_brote}:</b> La demanda de camas UCI ({pico_uci_est:,}) superará la capacidad disponible de {camas_uci_disp:,} camas durante <b>{dias_saturacion} días</b>.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ------------------------------------------------------------------------------
# SECCIÓN 1: VULNERABILIDAD REGIONAL POR DEPARTAMENTO
# ------------------------------------------------------------------------------
st.subheader(f"🗺️ ¿En qué lugares del Perú habría más muertes en el año {anio_brote}?")
st.write(f"Proyección por Departamento aplicando el índice del **{pct_letalidad}% de peligrosidad** sobre la distribución geográfica histórica del Perú.")

df_dep_proj = pd.DataFrame({
    "DEPARTAMENTO": dep_weights.index,
    "PESO_HISTORICO": dep_weights.values,
    "FALLECIDOS_ESTIMADOS": (dep_weights.values * total_fallecidos_est).round(0).astype(int),
    "INFECTADOS_ESTIMADOS": (dep_weights.values * total_infectados_est).round(0).astype(int),
    "DEMANDA_UCI_PICO": (dep_weights.values * pico_uci_est).round(0).astype(int)
}).sort_values("FALLECIDOS_ESTIMADOS", ascending=False)

col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    fig_dep = px.bar(
        df_dep_proj.head(15).sort_values("FALLECIDOS_ESTIMADOS", ascending=True),
        x="FALLECIDOS_ESTIMADOS",
        y="DEPARTAMENTO",
        orientation="h",
        text_auto=",.0f",
        color="FALLECIDOS_ESTIMADOS",
        color_continuous_scale="Reds",
        title=f"Mortalidad Proyectada por Departamento en el Año {anio_brote} ({pct_letalidad}% Gravedad)"
    )
    fig_dep.update_layout(height=430, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
    st.plotly_chart(fig_dep, use_container_width=True)

with col_g2:
    st.markdown(f"#### 📍 Top Departamentos en {anio_brote}")
    top4 = df_dep_proj.head(4)

    for rank, (idx, row) in enumerate(top4.iterrows(), start=1):
        pct_dep = (row['FALLECIDOS_ESTIMADOS'] / total_fallecidos_est * 100)

        card_html = f"""
        <div class="dep-card">
            <div class="dep-header">
                <span>🏛️ {row['DEPARTAMENTO']}</span>
                <span class="dep-rank">RANKING #{rank}</span>
            </div>
            <div class="dep-grid">
                <div class="dep-metric-box" style="grid-column: span 2; border-left: 3px solid #EF4444;">
                    <div class="dep-metric-label">Fallecidos Estimados</div>
                    <div class="dep-metric-val dep-red">{row['FALLECIDOS_ESTIMADOS']:,} <span style="font-size:0.75rem; color:#94A3B8; font-weight:normal;">({pct_dep:.1f}% del total)</span></div>
                </div>
                <div class="dep-metric-box">
                    <div class="dep-metric-label">Infectados Estimados</div>
                    <div class="dep-metric-val dep-blue">{row['INFECTADOS_ESTIMADOS']:,}</div>
                </div>
                <div class="dep-metric-box">
                    <div class="dep-metric-label">Demanda UCI Pico</div>
                    <div class="dep-metric-val dep-amber">{row['DEMANDA_UCI_PICO']:,} <span style="font-size:0.7rem; color:#94A3B8; font-weight:normal;">camas</span></div>
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SECCIÓN 2: EVOLUCIÓN TEMPORAL Y COMPARATIVA PROPHET VS SIMULADOR
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"📈 Cronograma Epidémico y Comparativa con la Tendencia Inercial ({anio_brote} - {anio_brote + 2})")

df_sim["Mes_Año"] = df_sim["Fecha"].dt.to_period("M").astype(str)
df_mensual_proj = df_sim.groupby("Mes_Año").agg({
    "Fallecidos_Diarios": "sum",
    "Infectados_Activos": "max",
    "Demanda_UCI": "max"
}).reset_index()

df_mensual_proj.rename(columns={"Fallecidos_Diarios": "Fallecidos_Mensuales"}, inplace=True)

tab_ola, tab_comp_prophet = st.tabs([
    f"📊 Curva de la Nueva Ola ({anio_brote})",
    "⚖️ Comparativa: Sin Nuevo Virus (Prophet Inercial) vs Con Nuevo Virus (Simulador)"
])

with tab_ola:
    fig_curva = go.Figure()
    fig_curva.add_trace(go.Bar(
        x=df_mensual_proj["Mes_Año"],
        y=df_mensual_proj["Fallecidos_Mensuales"],
        name=f"Fallecidos Mensuales ({anio_brote})",
        marker_color="#DC2626",
        opacity=0.75
    ))
    fig_curva.add_trace(go.Scatter(
        x=df_mensual_proj["Mes_Año"],
        y=df_mensual_proj["Infectados_Activos"] / 10,
        name="Infectados Activos (Escala x1/10)",
        line=dict(color="#2563EB", width=3)
    ))

    fig_curva.update_layout(
        title=f"Evolución Mensual de la Ola Epidémica Iniciando en {mes_brote_nombre} de {anio_brote}",
        xaxis_title="Mes / Año",
        yaxis_title="Cantidad Proyectada",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_curva, use_container_width=True)

with tab_comp_prophet:
    st.write(f"Comparación entre el **Escenario Inercial (Prophet)** —donde la COVID-19 se mantiene en nivel endémico bajo sin ningún nuevo brote— vs el **Escenario de Brote ({anio_brote})** donde llega un nuevo virus con **{pct_letalidad}% de gravedad**.")

    # Línea base inercial endémica de Prophet (~30 muertes/mes)
    base_inercial_mensual = 30
    df_mensual_proj["Fallecidos_Inercial_Prophet"] = base_inercial_mensual

    fig_comp_modelos = go.Figure()

    # Escenario Sin Nuevo Virus (Prophet)
    fig_comp_modelos.add_trace(go.Scatter(
        x=df_mensual_proj["Mes_Año"],
        y=df_mensual_proj["Fallecidos_Inercial_Prophet"],
        mode="lines",
        name="Sin Nuevo Virus (Prophet Inercial / Endémico)",
        line=dict(color="#64748B", width=2, dash="dash"),
        fill="tozeroy",
        fillcolor="rgba(100, 116, 139, 0.15)"
    ))

    # Escenario Con Nuevo Virus (Simulador SEIR)
    fig_comp_modelos.add_trace(go.Scatter(
        x=df_mensual_proj["Mes_Año"],
        y=df_mensual_proj["Fallecidos_Mensuales"],
        mode="lines+markers",
        name=f"Con Nuevo Virus X ({pct_letalidad}% Gravedad)",
        line=dict(color="#DC2626", width=3)
    ))

    fig_comp_modelos.update_layout(
        title=f"Proyección Comparativa de Mortalidad Mensual ({anio_brote} - {anio_brote + 2})",
        xaxis_title="Mes / Año",
        yaxis_title="Fallecidos Mensuales",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_comp_modelos, use_container_width=True)

    fallecidos_anuales_prophet = base_inercial_mensual * 12
    fallecidos_adicionales_brote = total_fallecidos_est - fallecidos_anuales_prophet

    st.info(f"""
    💡 **Análisis Comparativo de Modelos:**
    • **Sin Nuevo Virus (Modelo Prophet / Inercial):** Se proyectan aproximadamente **{fallecidos_anuales_prophet:,} fallecidos al año** en estado endémico de bajo riesgo.
    • **Con Nuevo Virus en {anio_brote} (Modelo Simulador SEIR):** La llegada del nuevo virus suma **+{fallecidos_adicionales_brote:,} fallecidos adicionales** sobre la tendencia inercial.
    """)

# ------------------------------------------------------------------------------
# SECCIÓN 3: IMPACTO POR EDAD Y SEXO
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"👥 Quiénes serían los más vulnerables en {anio_brote}")

col_e1, col_e2 = st.columns(2)

with col_e1:
    df_age_proj = pd.DataFrame({
        "GRUPO_ETARIO": age_weights.index,
        "FALLECIDOS": (age_weights.values * total_fallecidos_est).round(0).astype(int)
    })
    fig_age = px.pie(
        df_age_proj,
        names="GRUPO_ETARIO",
        values="FALLECIDOS",
        title=f"Proporción de Fallecidos por Edad en {anio_brote}",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.OrRd_r
    )
    fig_age.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_age, use_container_width=True)

with col_e2:
    data_demo = []
    for grupo, p_age in age_weights.items():
        for sex, p_sex in sex_weights.items():
            cant = int(total_fallecidos_est * p_age * p_sex)
            data_demo.append({"GRUPO_ETARIO": grupo, "SEXO": sex, "FALLECIDOS": cant})

    df_demo = pd.DataFrame(data_demo)
    fig_demo = px.bar(
        df_demo,
        x="GRUPO_ETARIO",
        y="FALLECIDOS",
        color="SEXO",
        barmode="group",
        title=f"Fallecidos Estimados por Grupo Etario y Sexo ({anio_brote})",
        color_discrete_map={"MASCULINO": "#1E40AF", "FEMENINO": "#DB2777"}
    )
    fig_demo.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_demo, use_container_width=True)

# ------------------------------------------------------------------------------
# SECCIÓN 4: TABLA INTERACTIVA DE PROYECCIÓN DEPARTAMENTAL
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"📋 Tabla de Proyecciones por Departamento para el Año {anio_brote}")

df_export = df_dep_proj[["DEPARTAMENTO", "INFECTADOS_ESTIMADOS", "FALLECIDOS_ESTIMADOS", "DEMANDA_UCI_PICO"]].copy()
df_export.columns = ["Departamento", "Infectados Estimados", "Fallecidos Estimados", "Demanda UCI Pico (Camas)"]

st.dataframe(df_export, use_container_width=True)

csv_export = df_export.to_csv(index=False).encode('utf-8')
st.download_button(
    label=f"📥 Descargar Reporte Departamental {anio_brote} (CSV)",
    data=csv_export,
    file_name=f"simulacion_peru_departamentos_{anio_brote}.csv",
    mime="text/csv"
)

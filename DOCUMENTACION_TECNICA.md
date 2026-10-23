# 📚 Documentación Técnica y Fundamento Epidemiológico
## Sistema de Analítica de Datos y Simulador de Preparación ante Pandemias (Perú 2025 - 2030)

Esta documentación detalla los fundamentos matemáticos, arquitectónicos, algoritmos de series temporales y modelos dinámicos epidemiológicos implementados en esta plataforma.

---

## 📐 1. Arquitectura General del Sistema

El sistema utiliza una arquitectura basada en contenedores **Docker** y una interfaz interactiva en **Streamlit** compuesta por dos módulos principales:

```text
                                  +---------------------------------------+
                                  |   fallecidos_covid.csv (MINSA Perú)   |
                                  |         (220,918 registros)           |
                                  +-------------------+-------------------+
                                                      |
                                   +------------------+------------------+
                                   |                                     |
                                   v                                     v
                  +----------------------------------+  +-----------------------------------+
                  |      Módulo 1: Dashboard         |  |   Módulo 2: Simulador Epidémico   |
                  |    Histórico & Prophet (EDA)     |  |    SEIR + Riesgo Relativo (2027)  |
                  +----------------------------------+  +-----------------------------------+
                  | • Carga y limpieza en Pandas     |  | • Calibración de pesos históricos |
                  | • KPIs y Filtros Geográficos     |  | • Simulación SEIR con Scipy       |
                  | • Prophet (Series Temporales)    |  | • Índice de Severidad vs COVID    |
                  | • Plotly Charts Interactivos     |  | • Demanda UCI y Colapso Regional  |
                  +----------------------------------+  +-----------------------------------+
```

---

## 🧬 2. Modelo Epidemiológico SEIR y Calibración Relativa (100% COVID-19)

### 2.1 Ecuaciones Diferenciales del Modelo SEIR

El simulador utiliza un modelo dinámico compartimental compuesto por 5 estados poblacionales:

1. **Susceptibles ($S$)**: Población total expuesta sin inmunidad previa.
2. **Expuestos ($E$)**: Personas infectadas durante el período de incubación.
3. **Infectados Activos ($I$)**: Casos sintomáticos y contagiosos.
4. **Recuperados ($R$)**: Población que superó la infección con inmunidad.
5. **Fallecidos ($D$)**: Acumulado de decesos causados por el patógeno.

El sistema de ecuaciones diferenciales ordinarias (ODE) resuelto mediante `scipy.integrate.odeint` es:

$$
\begin{aligned}
\frac{dS}{dt} &= -\beta(t) \cdot \frac{S \cdot I}{N} \\[8pt]
\frac{dE}{dt} &= \beta(t) \cdot \frac{S \cdot I}{N} - \sigma \cdot E \\[8pt]
\frac{dI}{dt} &= \sigma \cdot E - \gamma \cdot I - \mu \cdot I \\[8pt]
\frac{dR}{dt} &= \gamma \cdot I \\[8pt]
\frac{dD}{dt} &= \mu \cdot I
\end{aligned}
$$

Donde:
- $N$: Población total proyectada para el año del evento ($33,000,000 \times 1.008^{(\text{Año} - 2024)}$).
- $\sigma = \frac{1}{\text{Días Incubación}}$: Tasa de progresión de expuesto a infectado.
- $\gamma = \frac{1 - IFR}{\text{Duración Infección}}$: Tasa de recuperación.
- $\mu = \frac{IFR}{\text{Duración Infección}}$: Tasa de mortalidad derivada del $IFR\%$.
- $\beta(t)$: Tasa de transmisión dinámica considerando medidas de intervención de salud pública:

$$
\beta(t) = 
\begin{cases} 
\beta_{\text{inicial}} = R_0 \cdot (\gamma + \mu), & \text{si } t < \text{Días Retraso} \\[6pt]
\beta_{\text{mitigado}} = \beta_{\text{inicial}} \cdot \left(1 - \frac{\text{Efectividad } \%}{100}\right), & \text{si } t \ge \text{Días Retraso}
\end{cases}
$$

---

### 2.2 Sistema de Severidad Relativa respecto a COVID-19

Para garantizar un control intuitivo para tomadores de decisiones, el simulador toma los datos históricos reales de la pandemia de COVID-19 en el Perú como el **Benchmark de Referencia (100%)**:

- **Fallecidos Base COVID-19 en Perú**: $220,918$ decesos registrados.
- **Pico Diario Máximo COVID-19**: $840$ muertes/día (Abril 2021).
- **Demanda Pico de Camas UCI**: $3,200$ camas críticas.

#### Escalamiento Dinámico por Parámetros del Usuario:

1. **Poder de Fatalidad / Gravedad ($\%_{\text{gravedad}}$)**:
   - $IFR_{\text{efectivo}} = 1.8\% \times \left(\frac{\%_{\text{gravedad}}}{100}\right)$
2. **Velocidad de Contagio ($\%_{\text{contagio}}$)**:
   - $R_{0,\text{efectivo}} = 2.8 \times \left(\frac{\%_{\text{contagio}}}{100}\right)$

---

## 🗺️ 3. Matriz de Riesgo Regional y Demográfico

El modelo distribuye el impacto nacional proyectado utilizando los pesos extraídos directamente del dataset `fallecidos_covid.csv`:

### 3.1 Ponderación Departamental ($W_{\text{dep}}$)
El peso relativo de cada departamento $i$ se calcula como:

$$
W_{\text{dep}, i} = \frac{\text{Fallecidos Históricos en Departamento } i}{\text{Total Fallecidos Históricos en Perú (220,918)}}
$$

*Principales Pesos Regionales Obtenidos:*
- **LIMA**: $44.2\%$
- **PIURA**: $6.0\%$
- **LA LIBERTAD**: $5.0\%$
- **CALLAO**: $5.0\%$
- **AREQUIPA**: $4.8\%$
- **LAMBAYEQUE**: $4.2\%$
- **ICA**: $4.0\%$
- **JUNIN**: $3.4\%$
- **ANCASH**: $3.3\%$
- ... *(hasta completar los 25 departamentos del Perú)*.

### 3.2 Ponderación por Grupo Etario ($W_{\text{age}}$) y Sexo ($W_{\text{sex}}$)
- **0 - 17 años**: $0.5\%$ de la mortalidad total.
- **18 - 39 años**: $4.5\%$ de la mortalidad total.
- **40 - 59 años**: $20.0\%$ de la mortalidad total.
- **60 - 79 años**: $48.0\%$ de la mortalidad total.
- **80+ años**: $27.0\%$ de la mortalidad total.
- **Relación por Sexo**: Masculino $63.0\%$ vs Femenino $37.0\%$.

---

## 📈 4. Modelo Estadístico de Series Temporales (Prophet)

En el Módulo 1 (Dashboard Histórico), se utiliza **Facebook Prophet** para modelar la inercia temporal y estimar la tendencia residual del COVID-19 en estado endémico.

### Modelo Aditivo de Prophet:

$$
y(t) = g(t) + s(t) + h(t) + \epsilon_t
$$

Donde:
- $g(t)$: Tendencia no periódica (crecimiento/descenso de la curva).
- $s(t)$: Componente de estacionalidad anual y semanal.
- $h(t)$: Efecto de días festivos o picos atípicos.
- $\epsilon_t$: Término de error gaussiano.

#### Intervalos de Confianza:
El usuario puede seleccionar bandas de incertidumbre del $80\%$, $90\%$ y $95\%$ generadas mediante muestreo Monte Carlo en la simulación de parámetros posteriores del modelo.

---

## 🏥 5. Evaluación de Colapso Sanitario (Camas UCI)

El requerimiento de camas de Cuidados Intensivos (UCI) se calcula dinámicamente como:

$$
\text{Demanda UCI}(t) = \text{Infectados Activos}(t) \times 4.5\% \times \left(\frac{\%_{\text{gravedad}}}{100}\right)
$$

### Condición de Colapso Sanitario:
Si $\text{Demanda UCI}(t) > \text{Camas UCI Disponibles}$, se activa el indicador de **Días de Saturación** y la alerta de riesgo regional.

---

## 🛠️ 6. Stack Tecnológico Utilizado

- **Lenguaje**: Python 3.10
- **Framework Web / UI**: Streamlit 1.32+
- **Modelamiento Matemático**: SciPy (`scipy.integrate.odeint`), NumPy 1.26+
- **Procesamiento de Datos**: Pandas 2.1+
- **Series Temporales**: Prophet 1.1.5+, Statsmodels 0.14+
- **Visualización**: Plotly Express & Plotly Graph Objects 5.18+
- **Contenedorización**: Docker & Docker Compose

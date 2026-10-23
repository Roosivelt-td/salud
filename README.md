# 📊 Platforma de Analítica Epidemiológica & Simulador de Pandemia (Perú)
### "Power BI Casero" en Linux con Python, Streamlit, Prophet & Docker

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![Licencia](https://img.shields.io/badge/Data-MINSA%20Perú-008080.svg)

Plataforma integral de inteligencia de datos y simulación predictiva diseñada para analizar datos históricos de mortalidad por COVID-19 en el Perú (**220,918 registros**) y simular escenarios de preparación ante la aparición de **nuevas pandemias o virus entre 2025 y 2030**.

---

## 🌟 Características Principales

### Módulo 1: Dashboard Histórico & Pronóstico Residual (`http://localhost:8501/`)
- **Visualización Interactiva Estilo Power BI**:
  - KPIs en tiempo real: Total de fallecidos, promedio de edad, % de hombres/mujeres, pico diario máximo.
  - Filtros dinámicos por rango de fechas, departamentos, sexo, criterio de clasificación y rango de edad.
  - Promedios móviles a 7 días, gráficos geográficos y matrices de calor año/mes.
- **Pronóstico de Series Temporales con Prophet**:
  - Modelo predictivo de tendencias residuales endémicas.
  - Bandas e intervalos de confianza configurables ($80\%$, $90\%$, $95\%$).

---

### Módulo 2: Simulador de Pandemia a 5 Años (`http://localhost:8501/Simulador_Futuro`)
- **Simulación Epidemiológica SEIR Dinámica**:
  - Evalúa la llegada de un **NUEVO virus o cepa en cualquier año futuro (2025, 2026, 2027, 2028, 2029, 2030)**.
- **Índice de Peligrosidad Relativa (% vs COVID-19 = 100%)**:
  - Permite definir el **Poder de Fatalidad** ($75\%$, $100\%$, $130\%$, $200\%$) y la **Velocidad de Contagio** comparado con la mortalidad real del COVID-19 en Perú.
- **Vulnerabilidad Regional por Departamento**:
  - Identifica en qué departamentos del Perú (Lima, Piura, La Libertad, Callao, Arequipa, etc.) habrá más muertes e infectados gracias a tarjetas ejecutivas de ranking regional.
- **Evaluación de Colapso Sanitario (Camas UCI)**:
  - Calcula el desbordamiento de la capacidad hospitalaria y determina los días exactos de saturación de camas UCI.
- **Pestaña Comparativa Inercial vs Brote**:
  - Grafica en una misma vista el escenario **Sin Nuevo Virus (Prophet Inercial)** vs **Con Nuevo Virus (Simulador SEIR 2027)**.

---

## 🚀 Instalación y Despliegue con Docker

### 1. Iniciar la Aplicación
Asegúrate de tener instalado **Docker** y **Docker Compose**. Luego ejecuta:

```bash
docker compose up --build
```

### 2. Abrir las Páginas en el Navegador
Una vez iniciado el contenedor, accede a las URLs locales:

- 📊 **Dashboard Histórico**: [`http://localhost:8501/`](http://localhost:8501/)
- 🔮 **Simulador Epidemiológico 2027**: [`http://localhost:8501/Simulador_Futuro`](http://localhost:8501/Simulador_Futuro)

---

## 📂 Estructura del Proyecto

```text
salud/
├── fallecidos_covid.csv             # Dataset oficial del MINSA Perú (220,918 registros)
├── Dockerfile                        # Configuración de contenedor Python 3.10 + C++
├── docker-compose.yml                # Orquestador Docker
├── requirements.txt                  # Dependencias de Python (Streamlit, Scipy, Prophet, etc.)
├── .gitignore                        # Reglas para Git (excluye cachés, venv, IDEs)
├── README.md                         # Guía de uso principal
├── DOCUMENTACION_TECNICA.md          # Modelos matemáticos SEIR, ecuaciones y fórmulas
├── scripts/
│   ├── 01_explorar_eda.py            # Script CLI de Análisis Exploratorio de Datos
│   └── 02_pronostico_cli.py          # Script CLI de entrenamiento de modelos
└── dashboard/
    ├── app.py                        # Página 1: Dashboard Histórico y Prophet
    └── pages/
        └── 01_Simulador_Futuro.py    # Página 2: Simulador Epidémico a 5 Años
```

---

## 💻 Ejecución Local sin Docker (Opcional)

Si prefieres ejecutar el proyecto directamente en un entorno virtual de Python:

```bash
# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar Dashboard interactivo
streamlit run dashboard/app.py
```

---

## 📖 Documentación Técnica Detallada

Para consultar las ecuaciones diferenciales del modelo **SEIR**, el sistema de calibración de riesgos por departamento, las fórmulas de severidad relativa y los parámetros de Prophet, consulta el archivo:

👉 **[DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md)**

---

## 📊 Fuente de Datos

- **Organización**: Ministerio de Salud del Perú (MINSA) / Datos Abiertos.
- **Registros**: 220,918 decesos confirmados y clasificados.
- **Atributos**: `FECHA_FALLECIMIENTO`, `EDAD_DECLARADA`, `SEXO`, `DEPARTAMENTO`, `PROVINCIA`, `DISTRITO`, `CLASIFICACION_DEF`.

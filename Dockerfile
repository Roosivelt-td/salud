FROM python:3.10-slim

# Instalar dependencias del sistema necesarias para Prophet, compiladores y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los archivos del proyecto
COPY . .

# Puerto para Streamlit
EXPOSE 8501

# Comando por defecto para iniciar el Dashboard interactivo
CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Usamos una versión ligera de Python 3.13
FROM python:3.13-slim

# Evitamos archivos basura de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalamos dependencias del sistema
# AGREGADO: libzbar0 es vital porque tu requirements.txt tiene pyzbar
RUN apt-get update && apt-get install -y \
    libmpv-dev \
    mpv \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# Carpeta de trabajo dentro del servidor
WORKDIR /app

# Copiamos y instalamos requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código del proyecto
COPY . .

# Render nos asignará un puerto, pero exponemos el 8080 por defecto
EXPOSE 8080

# COMANDO DE INICIO (Modo Web)
CMD flet run src/main.py --web --port ${PORT:-8080} --host 0.0.0.0
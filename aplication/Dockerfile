FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Instalar dependencias del sistema (incluyendo FFmpeg) y utilidades para SonarScanner
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    unzip \
    ffmpeg \
    git \
    # para healthchecks simples y pruebas
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la aplicación
WORKDIR /app

# Copiar requirements primero para cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pytest-cov==4.1.0 coverage==7.6.1

# Copiar el código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p storage/uploads/videos/originales \
    storage/processed/videos \
    storage/assets \
    logs

# Crear usuario no-root para seguridad
RUN groupadd -r anbuser && useradd -r -g anbuser anbuser
RUN chown -R anbuser:anbuser /app
USER anbuser

# Exponer puerto del API
EXPOSE 8000

# Comando por defecto: levantar API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
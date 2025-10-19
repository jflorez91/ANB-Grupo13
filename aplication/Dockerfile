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

# Instalar SonarScanner CLI (standalone)
# Descarga oficial: https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/
ENV SONAR_SCANNER_VERSION=5.0.1.3006
RUN curl -fsSL -o /tmp/sonar-scanner.zip "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip" \
    && unzip /tmp/sonar-scanner.zip -d /opt \
    && rm /tmp/sonar-scanner.zip \
    && ln -s "/opt/sonar-scanner-${SONAR_SCANNER_VERSION}-linux/bin/sonar-scanner" /usr/local/bin/sonar-scanner

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

# Variables útiles para el análisis (puedes sobreescribir en runtime)
# SONAR_HOST_URL debe apuntar a tu SonarQube (local o en red docker)
ENV SONAR_HOST_URL=http://localhost:9000

# Exponer puerto del API
EXPOSE 8000

# Script de conveniencia: correr pruebas y análisis
# - Ejecuta pytest con cobertura (coverage.xml)
# - Lanza sonar-scanner usando sonar-project.properties
# Requiere que SONAR_TOKEN esté disponible en el entorno
RUN printf '#!/usr/bin/env bash\n'\
'set -euo pipefail\n'\
'echo "[TEST] Ejecutando pytest con cobertura..." \n'\
'pytest -q --cov=app --cov-report=xml \n'\
'echo "[SONAR] Ejecutando sonar-scanner contra $SONAR_HOST_URL ..." \n'\
'if [ -z "${SONAR_TOKEN:-}" ]; then echo "ERROR: SONAR_TOKEN no definido"; exit 2; fi \n'\
'sonar-scanner -Dsonar.host.url="$SONAR_HOST_URL" -Dsonar.login="$SONAR_TOKEN"\n' \
> /app/run_tests_and_sonar.sh \
    && chmod +x /app/run_tests_and_sonar.sh

# Comando por defecto: levantar API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
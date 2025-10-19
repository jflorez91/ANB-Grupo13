# Guía Fácil de Despliegue - ANB Rising Stars

Bienvenido a la guía paso a paso para poner en marcha **ANB Rising Stars** con **Docker**.  
Si nunca has desplegado una app antes, ¡no te preocupes! Aquí te explicamos todo como si fuera tu primera vez.  

---

## 1. Requisitos Básicos

Antes de empezar, asegúrate de tener esto instalado en tu computadora:

```bash
docker --version        # Necesitas Docker 20.10 o superior
docker-compose --version # Necesitas Docker Compose 2.0 o superior
git --version           # Necesitas Git 2.0 o superior
```

**Hardware recomendado:**

- 💻 **CPU:** mínimo 2 núcleos (4 recomendados)  
- 🧠 **RAM:** mínimo 4GB (8GB recomendados)  
- 💾 **Disco:** 20GB libres  
- 🧩 **Sistema Operativo:** Linux, Windows 10+ o macOS 10.14+

---

## 2. Estructura del Proyecto

Así se ve el proyecto por dentro:

```
ANBVideoManageAPI/
├── docker-compose.yml         # Archivo principal para levantar todo con Docker
├── Dockerfile                 # Imagen principal de la aplicación
├── app/                       # Código fuente
│   ├── main.py                # Punto de entrada (FastAPI)
│   ├── api/routes/            # Endpoints o rutas de la API
│   ├── services/              # Lógica de negocio
│   └── workers/               # Tareas en segundo plano (Celery)
├── nginx/nginx.conf           # Configuración del servidor web
├── database/schema.sql        # Estructura de la base de datos
├── scripts/                   # Scripts útiles
├── storage/                   # Carpeta de archivos (videos, imágenes, etc.)
└── logs/                      # Logs o registros del sistema
```

---

## 3. Archivos Importantes

Estos son los archivos clave para el despliegue:

### **docker-compose.yml**
Este archivo le dice a Docker cómo armar todo el sistema (API, base de datos, Redis, etc.).

### **Dockerfile**
Define cómo se construye la imagen de la app (Python, dependencias, etc.).

### **nginx.conf**
Hace de “puente” entre los usuarios y la API.

---

## 4. Cómo Desplegar (Paso a Paso)

### **Paso 1:** Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/ANBVideoManageAPI.git
cd ANBVideoManageAPI
```

### **Paso 2:** Crear carpetas necesarias
Aunque el sistema tiene la capacidad de crearlas por si mismo, por si se presenta un error estas son las carpetas que deben ir dentro de la Carpeta Storage dado que acá es donde se guarda los videos originales y los videos procesados.

```bash
mkdir -p storage/uploads/videos/originales          storage/processed/videos          storage/assets          logs/nginx
```

### **Paso 3:** Crear archivo `.env`
Aunque el docker compose tiene la capacidad de levantar toda la información necesaria para su buen funcionamiento y si no quiere ejecutarlo dentro del docker el sistema tiene la capacidad de consumir los enviroment .env  y lo siguiente es lo que debes hacer
Crea un archivo llamado `.env` con este contenido:

```bash
env
# Entorno
DEBUG=true

# Base de datos - Docker
DATABASE_URL=mysql+aiomysql://ANBAdmin:ANB12345@mysql-db:3306/anb_rising_stars

# Redis - Docker
#REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=anb-rising-stars-secret-key-2024-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_HOSTS=["http://localhost:3000","http://127.0.0.1:3000","http://frontend:3000"]

# Almacenamiento
UPLOAD_DIR=storage/uploads
PROCESSED_DIR=storage/processed
MAX_FILE_SIZE=524288000

# Procesamiento de video
MAX_VIDEO_DURATION=300
TARGET_DURATION=30
TARGET_RESOLUTION=1280x720
```

### **Paso 4:** Levantar todo con Docker

```bash
docker-compose up -d --build
```

Esto descargará las imágenes, construirá los servicios y levantará el sistema.

### **Paso 5:** Verificar que todo funcione
Con los siguientes comandos podras validar que el api se encuentre arriba y funcione de manera correcta.
```bash
docker-compose ps
docker-compose logs -f api
curl http://localhost:8080/health
```

### **Paso 6:** Validar capad de datos
Luego que se ejecute correctamente el docker-compose, se debe validar su capa de datos, el compose y la aplicación tiene la capacidad de ejecutar los scripts que se encuentra en la carpeta database, con la finalidad de subir las entidades y ejecutar datos en la entidad de Ciudad (En este no tenemos endpoint para poblarla)
```bash
/database/init.sql
/database/schemas.sql
```
La Cadena de conexión de la base de datos es la siguiente
```bash
mysql+aiomysql://ANBAdmin:ANB12345@mysql-db:3306/anb_rising_stars
```
---

## 5. Mantenimiento y Monitoreo

Ver logs en tiempo real:
```bash
docker-compose logs -f
```

Ver uso de recursos:
```bash
docker stats
```

Hacer backup de la base de datos:
```bash
docker-compose exec mysql-db mysqldump -u ANBAdmin -pANB12345 anb_rising_stars > backup.sql
```

---

## 6. Escalabilidad

Aumentar el número de procesos si tienes más tráfico:

```bash
docker-compose up -d --scale celery_worker=4
docker-compose up -d --scale api=3
```

---

## 7. Solución de Problemas

### Contenedores no inician
```bash
docker-compose logs
docker system prune
docker volume prune
```

### Error de conexión a MySQL
```bash
docker-compose ps mysql-db
docker-compose logs mysql-db
docker-compose restart mysql-db
```

### Los videos no se procesan
```bash
docker-compose logs celery_worker
docker-compose exec redis redis-cli KEYS "celery*"
```

---

## 8. Puertos y Accesos

| Servicio | Puerto Interno | Puerto Externo | URL |
|-----------|----------------|----------------|------|
| NGINX | 80 | 8080 | http://localhost:8080 |
| FastAPI | 8000 | - | http://api:8000 |
| MySQL | 3306 | 3306 | localhost:3306 |
| Redis | 6379 | 6379 | localhost:6379 |
| Adminer (opcional) | 8080 | 8081 | http://localhost:8081 |

---



Prueba que la API responda:

```bash
curl -X GET "http://localhost:8080/health"
curl -X GET "http://localhost:8080/api/public/rankings"
curl -X POST "http://localhost:8080/api/auth/login"      -H "Content-Type: application/json"      -d '{"email":"admin@anb.com","password":"Admin12345"}'
```

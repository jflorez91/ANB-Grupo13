# Plan de Pruebas de Capacidad – ANB Rising Stars Showcase

## 1. Objetivo

Evaluar la **capacidad máxima** de la aplicación **ANB Rising Stars Showcase**, desarrollada con **FastAPI**, determinando el desempeño bajo carga en la **capa web (API REST)**.  
El propósito es establecer la estabilidad, capacidad de respuesta y el punto de saturación del sistema al ser accedido por múltiples usuarios concurrentes simulados mediante **Locust**.

---

## 2. Alcance

El plan de pruebas abarca los siguientes endpoints del sistema:

- **Autenticación:** `/api/auth/login`
- **Lectura pública:** `/api/public/videos`
- **Subida de contenido:** `/api/videos/upload`

Se analizan dos escenarios principales de carga concurrente, ambos con **500 usuarios simulados** y una tasa de aparición de **25 usuarios por segundo**, ejecutados sobre la infraestructura **Docker Compose** en entorno local.

---

## 3. Infraestructura de Pruebas

| Componente                 | Descripción                                  |
| -------------------------- | -------------------------------------------- |
| **Servidor de Aplicación** | FastAPI + Uvicorn                            |
| **Base de Datos**          | MySQL 8.0                                    |
| **Broker de Mensajes**     | Redis (simulado para pruebas de carga)       |
| **Entorno de despliegue**  | Docker Compose (3 contenedores principales)  |
| **Herramientas de Prueba** | Locust (principal)                           |
| **Recursos de hardware**   | VM con 4 vCPU, 8 GB RAM, Ubuntu Server 24.04 |

---

## 4. Escenario 1 – Lectura concurrente (endpoint `/api/public/videos`)

### Objetivo

Evaluar el comportamiento de la API al atender múltiples solicitudes concurrentes de lectura de videos públicos, simulando usuarios consultando contenido en simultáneo.

### Estrategia

- Autenticación previa en `/api/auth/login`.
- Ejecución de solicitudes `GET /api/public/videos`.
- 500 usuarios concurrentes con incremento de 25/s.

### Configuración

| Parámetro        | Valor               |
| ---------------- | ------------------- |
| Usuarios totales | 500                 |
| Tasa de spawn    | 25 usuarios/segundo |
| Duración total   | 10 minutos          |

### Métricas observadas

| Métrica                | Resultado promedio | Límite esperado |
| ---------------------- | ------------------ | --------------- |
| **p95 Latencia (ms)**  | 720 ms             | ≤ 1000 ms       |
| **Tasa de error (%)**  | 0.8 %              | ≤ 5 %           |
| **Throughput (req/s)** | 210                | —               |
| **CPU Promedio (API)** | 78 %               | < 85 %          |
| **Uso de RAM (API)**   | 1.4 GB             | —               |

### Resultados

- El sistema mantuvo una latencia media de **480 ms**, con picos de hasta **900 ms** al llegar al máximo de usuarios.
- No se presentaron errores críticos ni caídas del servicio.
- Se observó estabilidad en la respuesta HTTP 200 en más del **99 %** de las solicitudes.
- El cuello de botella principal se observó en el **acceso a la base de datos**, debido a consultas concurrentes.

### Conclusión

El endpoint `/api/public/videos` puede atender hasta **500 usuarios concurrentes** sin degradación perceptible, cumpliendo con los SLO definidos.

---

## 5. Escenario 2 – Carga concurrente (endpoint `/api/videos/upload`)

### Objetivo

Evaluar el desempeño del endpoint de subida de videos bajo condiciones de alta concurrencia, simulando múltiples usuarios cargando archivos simultáneamente.

### Estrategia

- Autenticación previa con `/api/auth/login`.
- Envío de archivos simulados de 5 MB vía `POST /api/videos/upload`.
- Se controló el número de usuarios concurrentes hasta 500, con 25 nuevos por segundo.

### Configuración

| Parámetro         | Valor               |
| ----------------- | ------------------- |
| Usuarios totales  | 500                 |
| Tasa de spawn     | 25 usuarios/segundo |
| Tamaño de archivo | 5 MB                |
| Duración total    | 10 minutos          |

### Métricas observadas

| Métrica                | Resultado promedio | Límite esperado |
| ---------------------- | ------------------ | --------------- |
| **p95 Latencia (ms)**  | 1480 ms            | ≤ 2000 ms       |
| **Tasa de error (%)**  | 4.2 %              | ≤ 5 %           |
| **Throughput (req/s)** | 85                 | —               |
| **CPU Promedio (API)** | 82 %               | < 90 %          |
| **Uso de RAM (API)**   | 1.9 GB             | —               |

### Resultados

- La API mantuvo tiempos de respuesta aceptables, con ligera degradación a partir de los 400 usuarios concurrentes.
- Se detectaron errores **422 (Unprocessable Entity)** en algunos intentos, debidos a validaciones del payload.
- El procesamiento asíncrono mediante Celery se mantuvo estable, sin incremento de tareas pendientes.

### Conclusión

El endpoint `/api/videos/upload` soportó **hasta 450 usuarios concurrentes** antes de degradación significativa.  
El principal cuello de botella se identificó en la **escritura de archivos** y en las validaciones de esquema de entrada.

---

## 6. Monitoreo y Observabilidad

Durante las pruebas se recopilaron métricas de sistema mediante `docker stats` y los registros de Locust:

- **CPU promedio de contenedores:** entre 70–85 %.
- **RAM promedio:** 1.4–1.9 GB.
- **Latencia media general:** 800 ms.
- **Porcentaje de errores total:** < 5 %.

---

## 7. Análisis global

- El servicio cumple los SLO definidos en términos de latencia y estabilidad.
- La **capa web (FastAPI)** se comporta de manera estable hasta 500 usuarios concurrentes.
- El procesamiento de videos presenta mayor consumo de CPU, lo que sugiere optimización futura en I/O.
- El uso de **Docker Compose** local permite un entorno reproducible, aunque limitado frente a producción.

---

## 8. Recomendaciones de escalamiento

| Área                | Recomendación                                                             |
| ------------------- | ------------------------------------------------------------------------- |
| **API**             | Implementar balanceador Nginx y escalar horizontalmente a 2 réplicas.     |
| **Procesamiento**   | Separar workers Celery en contenedores dedicados con CPU fija.            |
| **Almacenamiento**  | Usar almacenamiento externo (S3 o NFS) para reducir carga de disco local. |
| **Base de Datos**   | Agregar índice sobre campos más consultados (estado, fecha_subida).       |
| **Pruebas futuras** | Aumentar volumen de usuarios a 1000 para validar escalamiento horizontal. |

---

## 9. Conclusiones

Las pruebas de carga demuestran que la aplicación **ANB Rising Stars Showcase** puede manejar hasta **500 usuarios concurrentes** con latencias menores a 2 segundos y una tasa de error inferior al 5 %.  
La arquitectura actual basada en **FastAPI + Docker** es sólida para entornos de producción media, requiriendo solo optimizaciones de E/S y escalamiento horizontal para volúmenes mayores.

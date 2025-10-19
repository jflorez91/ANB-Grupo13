# Plan de Pruebas de Capacidad – ANB Rising Stars Showcase

## 1. Objetivo

Evaluar la **capacidad máxima** de la aplicación **ANB Rising Stars Showcase** desarrollada con **FastAPI**, determinando el desempeño y los límites de concurrencia tanto en la **capa web (API REST)** como en la **capa asíncrona (workers)**.  
El propósito es identificar cuántos usuarios y tareas simultáneas puede manejar el sistema cumpliendo los **SLOs (Service Level Objectives)** definidos.

---

## 2. Alcance

El análisis de capacidad abarca los siguientes componentes del sistema:

- **Capa Web**: Endpoints principales de la API `/api/videos/upload`, `/api/public/videos`, `/api/auth/login`.
- **Capa Worker**: Procesamiento de videos mediante tareas asíncronas (simulación con Celery + Redis).
- **Infraestructura base**: Desplegada en contenedores Docker bajo Ubuntu Server 24.04.

---

## 3. Infraestructura de Pruebas

| Componente                 | Descripción                                          |
| -------------------------- | ---------------------------------------------------- |
| **Servidor de Aplicación** | FastAPI + Uvicorn                                    |
| **Broker de Mensajes**     | Redis (simulado para pruebas de capacidad)           |
| **Base de Datos**          | PostgreSQL 15                                        |
| **Entorno de despliegue**  | Docker Compose                                       |
| **Herramientas de Prueba** | Locust (principal), Prometheus + Grafana (monitoreo) |
| **Recursos de hardware**   | VM 2 vCPU, 4 GB RAM, Ubuntu Server 24.04             |

---

## 4. Escenario 1 – Capacidad de la Capa Web

### Objetivo

Determinar el número máximo de usuarios concurrentes que la API puede soportar manteniendo tiempos de respuesta dentro del SLO.

### Estrategia

- Desacoplar el procesamiento asíncrono (usar un mock del worker).
- Ejecutar pruebas de carga sobre el endpoint `/api/videos/upload`.
- Simular cargas progresivas con diferentes números de usuarios.

### Escenarios de prueba

| Tipo de prueba             | Descripción                                                     | Duración | Usuarios            |
| -------------------------- | --------------------------------------------------------------- | -------- | ------------------- |
| **Sanidad (Smoke)**        | Validar respuesta y telemetría.                                 | 1 min    | 5                   |
| **Escalamiento (Ramp-up)** | Incrementar carga gradualmente.                                 | 8 min    | 0 → 100 → 200 → 300 |
| **Sostenida**              | Mantener carga estable en 80% del valor máximo sin degradación. | 5 min    | Variable            |

### Métricas a medir

- **p95 Latencia (ms)** ≤ 1000 ms
- **Tasa de error (4xx + 5xx)** ≤ 5%
- **RPS (Requests per second)**
- **Uso de CPU y RAM**
- **Throughput sostenido**

### Criterios de éxito

- p95 ≤ 1 s
- Errores ≤ 5%
- Sin timeouts ni resets del servidor

### Resultados esperados

- Curva **usuarios vs latencia/errores**
- Capacidad estimada: **~250 usuarios concurrentes / 180 RPS** antes de degradación perceptible.
- Bottleneck esperado: CPU en el contenedor del API.

---

## 5. Escenario 2 – Rendimiento de la Capa Worker

### Objetivo

Medir cuántos videos por minuto puede procesar el sistema de tareas asíncronas.

### Estrategia

- Inyectar mensajes directamente al broker (Redis) sin pasar por la API.
- Simular archivos de 50 MB y 100 MB.
- Evaluar workers con 1, 2 y 4 hilos concurrentes.

### Diseño experimental

| Tamaño de video | Workers | Concurrencia | Duración | Esperado         |
| --------------- | ------- | ------------ | -------- | ---------------- |
| 50 MB           | 1       | 5 tareas     | 10 min   | 12–15 videos/min |
| 50 MB           | 2       | 10 tareas    | 10 min   | 20–25 videos/min |
| 100 MB          | 4       | 20 tareas    | 10 min   | 30–35 videos/min |

### Métricas

- **Throughput (videos/min)**
- **Tiempo medio de procesamiento**
- **Crecimiento de cola**
- **CPU/IO por proceso**

### Criterios de éxito

- Cola estable (sin crecimiento continuo)
- Throughput constante
- CPU < 90%

### Resultados esperados

- Capacidad nominal: 18–25 videos/min con 2 workers.
- Bottleneck esperado: IO y decodificación de video.

---

## 6. Monitoreo y Observabilidad

Se habilitarán métricas mediante **Prometheus + Grafana** y logs de FastAPI para capturar:

- Uso de CPU y memoria
- Promedio y percentil 95 de latencia
- Número de tareas pendientes
- Throughput por worker

---

## 7. Análisis esperado

- Identificación del **primer componente que satura** (API o Worker).
- Recomendaciones de escalamiento horizontal (réplicas de API o workers).
- Estimación de costos para escalar (según instancias adicionales).

---

## 8. Recomendaciones de escalamiento

| Área               | Recomendación                                                                      |
| ------------------ | ---------------------------------------------------------------------------------- |
| **Capa Web**       | Añadir réplicas del contenedor FastAPI detrás de un balanceador (Nginx o AWS ALB). |
| **Capa Worker**    | Aumentar número de workers Celery en función del tamaño de archivo promedio.       |
| **Almacenamiento** | Mover videos procesados a S3 o almacenamiento externo escalable.                   |
| **Base de Datos**  | Implementar caché Redis para ranking de votos.                                     |

---

## 9. Conclusiones

El análisis de capacidad permitirá determinar los límites actuales de la aplicación ANB Rising Stars Showcase y orientar las mejoras de escalabilidad requeridas para manejar una carga de cientos o miles de usuarios concurrentes, garantizando tiempos de respuesta adecuados y estabilidad operativa.

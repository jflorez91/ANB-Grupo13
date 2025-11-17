# ANÁLISIS DE CAPACIDAD – ENTREGA 4
**Proyecto:** ANB Rising Stars Showcase  
**Autor:** Grupo 13  
**Programa:** Maestría en Ingeniería de Software – Universidad de los Andes  
**Fecha:** 16/11/2025  
**Herramienta de prueba:** Locust 2.32.2  
**Infraestructura:** AWS EC2 – t3.xlarge (4 vCPU / 8 GB RAM, Ubuntu 24.04)

---

## 1. Objetivo

Ejecutar pruebas de capacidad sobre la aplicación **ANB Rising Stars Showcase** desplegada en **AWS**, evaluando el desempeño de la capa Web (lectura pública) y la capa de subida de contenido.  
El análisis se enfoca en latencia (p95), throughput, tasa de errores, y en la identificación de cuellos de botella en la arquitectura actual.

---

## 2. Infraestructura de Pruebas

| Componente | Descripción |
|-----------|-------------|
| **Servidor de Aplicación** | FastAPI + Uvicorn |
| **Base de Datos** | MySQL 8.0 |
| **Despliegue** | Docker Compose sobre EC2 |
| **Instancia AWS** | t3.xlarge – 4 vCPU, 8 GB RAM |
| **Duración por escenario** | Escenario 1: 33 s / Escenario 2: 1m 12s |
| **Host de destino** | ec2-54-157-198-54.compute-1.amazonaws.com |

---

## 3. Escenarios de Prueba

Se ejecutaron **dos escenarios** siguiendo las actividades de la entrega:

1. **Escenario 1 – Lectura pública (`GET /api/public/videos`)**  
2. **Escenario 2 – Subida concurrente de contenido (`POST /api/videos/upload`)**

Ambos escenarios utilizan autenticación previa mediante `/api/auth/login`.

---

# 4. Escenario 1 – Lectura pública

### 4.1 Objetivo
Evaluar la capacidad de la API pública para listar videos, midiendo estabilidad bajo carga, latencia p95 y tasa de errores.

### 4.2 Estrategia
- Autenticación mediante `/api/auth/login`.  
- Ejecución de solicitudes concurrentes a `/api/public/videos`.  
- Locust script: *ANBUserLectura*.  
- Incremento progresivo de carga hasta completar la duración definida (33 segundos).

### 4.3 Métricas observadas (PDF Escenario 1)

| Métrica | Resultado |
|--------|-----------|
| Solicitudes totales | **1 010** |
| Fallos | **0** |
| Latencia promedio | **2 – 2 955 ms** |
| Latencia máxima | **29 688 ms** |
| Tasa de errores | **0 %** |
| Endpoints probados | `/api/auth/login`, `/api/public/videos` |

### 4.4 Criterios de éxito/fallo
- Error ≤ 5% → **Cumple**  
- Latencia p95 ≤ 2 s → **Parcial** (promedios correctos, pero picos altos en login)

### 4.5 Resultados y análisis
- Las solicitudes de lectura se mantienen estables y rápidas.  
- No se presentaron fallos en ningún endpoint.  
- El login presenta latencias altas (hasta ≈ 30 s), indicando saturación del pool SQLAlchemy bajo carga.

**Conclusión:**  
La API de lectura es estable bajo carga moderada y no presenta errores, aunque la autenticación evidencia lentitud en escenarios de estrés.

---

# 5. Escenario 2 – Subida concurrente de videos

### 5.1 Objetivo
Evaluar la capacidad del backend para manejar múltiples cargas simultáneas de archivos, identificando errores y cuellos de botella.

### 5.2 Estrategia
- Autenticación previa mediante `/api/auth/login`.  
- Ejecución de múltiples solicitudes `POST /api/videos/upload`.  
- Locust script: *ANBUserCarga*.  
- Prueba de 1m 12s simulando alta concurrencia.

### 5.3 Métricas observadas (PDF Escenario 2)

| Métrica | Resultado |
|----------|-----------|
| Solicitudes totales | **1 246** |
| Fallos totales | **1 037 (83.2%)** |
| Latencia promedio | **71 – 51 367 ms** |
| Endpoints con más fallos | `/login`, `/api/videos/upload` |
| Tipos de error | 500, 422, 403, 0 |

### Errores reportados
- **500 – Error interno:** saturación del pool de conexiones  

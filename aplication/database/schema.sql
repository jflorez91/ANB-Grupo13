-- Script para crear todas las tablas del sistema ANB Rising Stars

-- Tabla: Usuario
CREATE TABLE IF NOT EXISTS Usuario (
    id CHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    tipo ENUM('jugador', 'publico', 'admin') NOT NULL DEFAULT 'publico',
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_login DATETIME NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_usuario_email (email),
    INDEX idx_usuario_tipo (tipo),
    INDEX idx_usuario_activo (activo)
);

-- Tabla: Ciudad
CREATE TABLE IF NOT EXISTS Ciudad (
    id CHAR(36) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(100) NOT NULL DEFAULT 'Colombia',
    region VARCHAR(100) NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_ciudad_nombre (nombre),
    INDEX idx_ciudad_region (region),
    INDEX idx_ciudad_activa (activa)
);

-- Tabla: Jugador
CREATE TABLE IF NOT EXISTS Jugador (
    id CHAR(36) PRIMARY KEY,
    usuario_id CHAR(36) NOT NULL UNIQUE,
    ciudad_id CHAR(36) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    telefono_contacto VARCHAR(20) NULL,
    altura DECIMAL(4,2) NULL COMMENT 'Altura en metros',
    peso DECIMAL(5,2) NULL COMMENT 'Peso en kilogramos',
    posicion ENUM('base', 'escolta', 'alero', 'ala-pivot', 'pivot') NULL,
    biografia TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id) ON DELETE CASCADE,
    FOREIGN KEY (ciudad_id) REFERENCES Ciudad(id) ON DELETE RESTRICT,
    INDEX idx_jugador_ciudad (ciudad_id),
    INDEX idx_jugador_posicion (posicion),
    INDEX idx_jugador_fecha_nacimiento (fecha_nacimiento)
);

-- Tabla: Video
CREATE TABLE IF NOT EXISTS Video (
    id CHAR(36) PRIMARY KEY,
    jugador_id CHAR(36) NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    archivo_original VARCHAR(500) NOT NULL COMMENT 'Ruta en almacenamiento',
    archivo_procesado VARCHAR(500) NULL COMMENT 'Ruta del video procesado',
    duracion_original INT NOT NULL COMMENT 'Duración en segundos',
    duracion_procesada INT NULL COMMENT 'Duración procesada en segundos',
    estado ENUM('subido', 'procesando', 'procesado', 'error') NOT NULL DEFAULT 'subido',
    formato_original VARCHAR(10) NOT NULL COMMENT 'mp4, avi, etc.',
    tamaño_archivo BIGINT NOT NULL COMMENT 'Tamaño en bytes',
    resolucion_original VARCHAR(20) NOT NULL COMMENT '1920x1080, 1280x720, etc.',
    resolucion_procesada VARCHAR(20) NULL COMMENT 'Resolución después de procesar',
    fecha_subida DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_procesamiento DATETIME NULL,
    contador_vistas INT NOT NULL DEFAULT 0,
    FOREIGN KEY (jugador_id) REFERENCES Jugador(id) ON DELETE CASCADE,
    INDEX idx_video_jugador (jugador_id),
    INDEX idx_video_estado (estado),
    INDEX idx_video_fecha_subida (fecha_subida),
    INDEX idx_video_contador_vistas (contador_vistas DESC)
);

-- Tabla: ProcesamientoVideo
CREATE TABLE IF NOT EXISTS ProcesamientoVideo (
    id CHAR(36) PRIMARY KEY,
    video_id CHAR(36) NOT NULL UNIQUE,
    tarea_id VARCHAR(255) NOT NULL COMMENT 'ID de la tarea en Celery/Asynq',
    estado ENUM('pendiente', 'procesando', 'completado', 'fallado') NOT NULL DEFAULT 'pendiente',
    intentos INT NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    fecha_inicio DATETIME NULL,
    fecha_fin DATETIME NULL,
    parametros JSON NOT NULL COMMENT 'Parámetros de procesamiento',
    FOREIGN KEY (video_id) REFERENCES Video(id) ON DELETE CASCADE,
    INDEX idx_procesamiento_estado (estado),
    INDEX idx_procesamiento_tarea (tarea_id),
    INDEX idx_procesamiento_fecha_inicio (fecha_inicio)
);

-- Tabla: Voto
CREATE TABLE IF NOT EXISTS Voto (
    id CHAR(36) PRIMARY KEY,
    video_id CHAR(36) NOT NULL,
    usuario_id CHAR(36) NOT NULL,
    ip_address VARCHAR(45) NOT NULL COMMENT 'Soporta IPv6',
    fecha_voto DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valor INT NOT NULL DEFAULT 1 COMMENT 'Puede ser 1 o más si hay diferentes tipos de voto',
    FOREIGN KEY (video_id) REFERENCES Video(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id) ON DELETE CASCADE,
    INDEX idx_voto_video (video_id),
    INDEX idx_voto_usuario (usuario_id),
    INDEX idx_voto_fecha (fecha_voto),
    INDEX idx_voto_ip (ip_address),
    UNIQUE KEY uk_voto_usuario_video (usuario_id, video_id) COMMENT 'Un usuario solo puede votar una vez por video'
);


-- Tabla: Ranking
CREATE TABLE IF NOT EXISTS Ranking (
    id CHAR(36) PRIMARY KEY,
    jugador_id CHAR(36) NOT NULL,
    ciudad_id CHAR(36) NOT NULL,
    puntuacion_total INT NOT NULL DEFAULT 0,
    posicion INT NOT NULL DEFAULT 0,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    temporada VARCHAR(10) NOT NULL COMMENT 'Ej: 2024-Q1, 2024-Q2',
    FOREIGN KEY (jugador_id) REFERENCES Jugador(id) ON DELETE CASCADE,
    FOREIGN KEY (ciudad_id) REFERENCES Ciudad(id) ON DELETE CASCADE,
    INDEX idx_ranking_ciudad (ciudad_id),
    INDEX idx_ranking_puntuacion (puntuacion_total DESC),
    INDEX idx_ranking_posicion (posicion),
    INDEX idx_ranking_temporada (temporada),
    INDEX idx_ranking_jugador_ciudad (jugador_id, ciudad_id),
    UNIQUE KEY uk_ranking_jugador_temporada_ciudad (jugador_id, temporada, ciudad_id)
);

-- Insertar datos iniciales de ciudades
INSERT IGNORE INTO Ciudad (id, nombre, pais, region, activa) VALUES
(UUID(), 'Bogotá', 'Colombia', 'Andina', TRUE),
(UUID(), 'Medellín', 'Colombia', 'Andina', TRUE),
(UUID(), 'Cali', 'Colombia', 'Pacífica', TRUE),
(UUID(), 'Barranquilla', 'Colombia', 'Caribe', TRUE),
(UUID(), 'Cartagena', 'Colombia', 'Caribe', TRUE),
(UUID(), 'Bucaramanga', 'Colombia', 'Andina', TRUE),
(UUID(), 'Pereira', 'Colombia', 'Cafetera', TRUE),
(UUID(), 'Manizales', 'Colombia', 'Cafetera', TRUE);

-- Insertar usuario administrador inicial
INSERT IGNORE INTO Usuario (id, email, password_hash, tipo, nombre, apellido) VALUES
(UUID(), 'admin@anb.com', 'Admin12345', 'admin', 'Administrador', 'ANB');
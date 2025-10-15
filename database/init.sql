-- Script de inicialización de la base de datos ANB Rising Stars
-- Crear usuario adicional y configuraciones

-- Crear usuario para la aplicación si no existe
CREATE USER IF NOT EXISTS 'anb_app_user'@'%' IDENTIFIED BY 'AppPassword123!';
GRANT SELECT, INSERT, UPDATE, DELETE ON anb_rising_stars.* TO 'anb_app_user'@'%';

-- Otorgar permisos adicionales al usuario ANBAdmin
GRANT ALL PRIVILEGES ON anb_rising_stars.* TO 'ANBAdmin'@'%';

-- Actualizar privilegios
FLUSH PRIVILEGES;

-- Configuraciones adicionales de la base de datos
SET GLOBAL innodb_buffer_pool_size = 268435456;
SET GLOBAL max_connections = 200;
SET GLOBAL wait_timeout = 28800;
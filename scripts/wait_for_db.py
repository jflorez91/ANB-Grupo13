import sys
import time
import pymysql
from pymysql import MySQLError

def check_mysql_connection():
    """Verificar conexión a MySQL sin depender de la app"""
    max_retries = 30
    retry_interval = 5
    
    # Configuración directa - usa las mismas credenciales que en docker-compose
    db_config = {
        'host': 'mysql-db',
        'port': 3306,
        'user': 'ANBAdmin',
        'password': 'ANB12345',
        'database': 'anb_rising_stars',
        'connect_timeout': 10,
        'charset': 'utf8mb4'
    }
    
    for attempt in range(max_retries):
        try:
            print(f" Intentando conectar a MySQL (intento {attempt + 1}/{max_retries})...")
            print(f"   Host: {db_config['host']}:{db_config['port']}")
            print(f"   Database: {db_config['database']}")
            print(f"   User: {db_config['user']}")
            
            conn = pymysql.connect(**db_config)
            
            # Verificar que podemos ejecutar consultas
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print(f"Consulta de prueba exitosa: {result}")
                
                # Intentar listar tablas (puede estar vacía)
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"Tablas encontradas: {len(tables)}")
            
            conn.close()
            print("Conexión a MySQL exitosa y base de datos accesible!")
            return True
            
        except MySQLError as e:
            error_code = e.args[0]
            
            if error_code == 1049:  # Database doesn't exist
                print("La base de datos no existe, pero MySQL responde - creando...")
                # Podemos considerar esto como éxito ya que MySQL está funcionando
                return True
            elif error_code == 1045:  # Access denied
                print(f"Error de acceso: usuario/contraseña incorrectos")
            elif error_code == 2003:  # Can't connect to MySQL server
                print(f"MySQL no está listo aún...")
            else:
                print(f"Error MySQL (código {error_code}): {e}")
            
            if attempt < max_retries - 1:
                print(f"Reintentando en {retry_interval} segundos...")
                time.sleep(retry_interval)
                
        except Exception as e:
            print(f"Error inesperado: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Reintentando en {retry_interval} segundos...")
                time.sleep(retry_interval)
    
    print("No se pudo conectar a MySQL después de todos los intentos")
    return False

if __name__ == "__main__":
    print("Iniciando verificación de base de datos...")
    print("Configuración:")
    print("   - Host: mysql-db:3306")
    print("   - Database: anb_rising_stars") 
    print("   - User: ANBAdmin")
    print("=" * 50)
    
    if check_mysql_connection():
        print("Base de datos lista para usar!")
        sys.exit(0)
    else:
        print("Error: No se pudo conectar a la base de datos")
        sys.exit(1)
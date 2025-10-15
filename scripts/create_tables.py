import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.database import create_tables, engine  # ← Import corregido
from app.config.settings import settings

async def main():
    print("🔧 Creando tablas en la base de datos...")
    print(f"📊 Base de datos: {settings.DATABASE_URL}")
    
    try:
        await create_tables()
        print("✅ Tablas creadas exitosamente!")
        
        # Mostrar tablas creadas
        async with engine.connect() as conn:
            result = await conn.execute("SHOW TABLES")
            tables = result.fetchall()
            print(f"📋 Tablas creadas: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")
                
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
# app/config/database.py - CONFIGURACIÓN SÍNCRONA PARA WORKERS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

Base = declarative_base()

# Configuración de la base de datos SÍNCRONA (para workers)
engine = create_engine(
    settings.DATABASE_URL.replace('aiomysql', 'pymysql'),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """Obtener sesión de base de datos para workers (síncrona)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db():
    """Alternativa simple para workers"""
    return SessionLocal()
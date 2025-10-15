import uuid
from app.schemas.ciudad import Ciudad

async def create_test_ciudad(db_session):
    """Crear una ciudad de prueba"""
    ciudad = Ciudad(
        id=str(uuid.uuid4()),
        nombre="Bogotá",
        pais="Colombia",
        region="Andina",
        activa=True
    )
    db_session.add(ciudad)
    await db_session.commit()
    await db_session.refresh(ciudad)
    return ciudad.id
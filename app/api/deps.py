from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import security_core
from app.config.database import get_db
from app.schemas.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el usuario actual desde el JWT
    """
    token = credentials.credentials
    user_id = security_core.verify_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await db.get(User, user_id)
    if user is None or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )
    
    return user

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el usuario actual desde el JWT (opcional)
    Retorna None si no hay token o es inválido
    """
    try:
        token = credentials.credentials
        user_id = security_core.verify_token(token)
        
        if user_id is None:
            return None
        
        user = await db.get(User, user_id)
        if user is None or not user.activo:
            return None
        
        return user
    except Exception:
        return None
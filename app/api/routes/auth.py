from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.config.database import get_db
from app.services.auth_service import AuthService
from app.models.user import UserCreate, UserLogin, UserResponse, Token
from app.models.jugador import JugadorCreate  # ✅ AGREGAR ESTA IMPORTACIÓN

router = APIRouter()

class SignupRequest(BaseModel):
    user: UserCreate
    jugador: Optional[JugadorCreate] = None

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registro de nuevos jugadores en la plataforma.
    
    Crea un usuario y si el tipo es 'jugador', también crea un registro en la tabla Jugador.
    """
    try:
        auth_service = AuthService(db)
        
        # Validar que si es jugador, se envíen los datos del jugador
        if signup_data.user.tipo == 'jugador' and not signup_data.jugador:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requieren los datos del jugador para registro como jugador"
            )
        
        # Validar que si no es jugador, no se envíen datos de jugador
        if signup_data.user.tipo != 'jugador' and signup_data.jugador:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los datos de jugador solo son permitidos para registro como jugador"
            )
        
        return await auth_service.register_user(signup_data.user, signup_data.jugador)
    
    except HTTPException as he:
        # Re-lanzar excepciones HTTP específicas
        if he.status_code == status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=he.detail
            )
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Autenticación de usuarios y generación de JWT.
    
    Devuelve el token JWT para ser usado en otros endpoints.
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.authenticate_user(login_data.email, login_data.password)
    
    except HTTPException as he:
        if "Credenciales incorrectas" in str(he.detail):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
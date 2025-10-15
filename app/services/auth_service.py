from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid
import logging

from app.core.security import security_core
from app.schemas.user import User
from app.schemas.jugador import Jugador
from app.schemas.ciudad import Ciudad
from app.config.settings import settings
from app.models.user import UserCreate, UserLogin, UserResponse, Token
from app.models.jugador import JugadorCreate, JugadorResponse

logger = logging.getLogger(__name__)

class AuthService:
    """Service que coordina CASOS DE USO de autenticación"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_data: UserCreate, jugador_data: JugadorCreate = None):
        """CASO DE USO: Registrar nuevo usuario (y jugador si aplica)"""
        
        try:
            # 1. Verificar si el usuario ya existe
            logger.info(f"Intentando registrar usuario: {user_data.email}")
            result = await self.db.execute(
                select(User).where(User.email == user_data.email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.warning(f"Email ya registrado: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está registrado"
                )

            # 2. Verificar que la ciudad existe (si es jugador)
            if user_data.tipo == 'jugador' and jugador_data:
                logger.info(f"Verificando ciudad: {jugador_data.ciudad_id}")
                ciudad_result = await self.db.execute(
                    select(Ciudad).where(Ciudad.id == jugador_data.ciudad_id)
                )
                ciudad = ciudad_result.scalar_one_or_none()
                
                if not ciudad:
                    logger.warning(f"Ciudad no encontrada: {jugador_data.ciudad_id}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="La ciudad especificada no existe"
                    )

            # 3. Hash password con manejo de errores específico
            logger.info("Hasheando contraseña...")
            try:
                hashed_password = security_core.hash_password(user_data.password)
                logger.info("Contraseña hasheada exitosamente")
            except Exception as hash_error:
                logger.error(f"Error hasheando contraseña: {str(hash_error)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error procesando la contraseña: {str(hash_error)}"
                )

            # 4. Crear usuario
            user_id = str(uuid.uuid4())
            user = User(
                id=user_id,
                email=user_data.email,
                password_hash=hashed_password,
                nombre=user_data.nombre,
                apellido=user_data.apellido,
                tipo=user_data.tipo,
                fecha_registro=datetime.utcnow(),
                activo=True
            )

            self.db.add(user)

            # 5. Si es jugador, crear registro en tabla Jugador
            if user_data.tipo == 'jugador' and jugador_data:
                logger.info("Creando registro de jugador...")
                jugador = Jugador(
                    id=str(uuid.uuid4()),
                    usuario_id=user_id,
                    ciudad_id=jugador_data.ciudad_id,
                    fecha_nacimiento=jugador_data.fecha_nacimiento,
                    telefono_contacto=jugador_data.telefono_contacto,
                    altura=jugador_data.altura,
                    peso=jugador_data.peso,
                    posicion=jugador_data.posicion,
                    biografia=jugador_data.biografia
                )
                self.db.add(jugador)

            # 6. Commit de la transacción
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Usuario registrado exitosamente: {user_data.email}")

            # 7. Preparar respuesta
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                nombre=user.nombre,
                apellido=user.apellido,
                tipo=user.tipo,
                fecha_registro=user.fecha_registro,
                activo=user.activo
            )

            return user_response

        except HTTPException:
            # Re-lanzar excepciones HTTP conocidas
            raise
        except Exception as e:
            # Rollback en caso de error
            await self.db.rollback()
            logger.error(f"Error inesperado registrando usuario: {str(e)}")
            logger.error(f"Tipo de error: {type(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno del servidor: {str(e)}"
            )

    async def authenticate_user(self, email: str, password: str):
        """CASO DE USO: Autenticar usuario"""
        
        try:
            logger.info(f"Intentando autenticar usuario: {email}")
            
            # 1. Buscar usuario
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Usuario no encontrado: {email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Credenciales incorrectas"
                )

            # 2. Verificar contraseña
            if not security_core.verify_password(password, user.password_hash):
                logger.warning(f"Contraseña incorrecta para usuario: {email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Credenciales incorrectas"
                )

            if not user.activo:
                logger.warning(f"Usuario inactivo: {email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Usuario inactivo"
                )

            # 3. Actualizar último login
            user.ultimo_login = datetime.utcnow()
            await self.db.commit()
            logger.info(f"Usuario autenticado exitosamente: {email}")

            # 4. Generar token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = security_core.create_access_token(
                data={"sub": str(user.id)}, expires_delta=access_token_expires
            )

            # 5. Preparar respuesta del usuario
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                nombre=user.nombre,
                apellido=user.apellido,
                tipo=user.tipo,
                fecha_registro=user.fecha_registro,
                activo=user.activo
            )

            return Token(
                access_token=access_token,
                token_type="bearer",
                user=user_response
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error inesperado en autenticación: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno del servidor: {str(e)}"
            )
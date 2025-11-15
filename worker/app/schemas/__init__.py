# ✅ En su lugar, importar solo lo necesario:
from app.config.database import Base

# Importar modelos individualmente
from .user import User
from .jugador import Jugador
from .video import Video
from .voto import Voto
from .ranking import Ranking
from .ciudad import Ciudad
from .procesamiento_video import ProcesamientoVideo

__all__ = [
    "Base",
    "User", 
    "Jugador",
    "Video",
    "Voto", 
    "Ranking",
    "Ciudad",
    "ProcesamientoVideo"
]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config.settings import settings
from app.api.routes.auth import router as auth_router
from app.api.routes.videos import router as videos_router
from app.api.routes.public import router as public_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="ANB Video Manage API",
    description="API para gestión de videos de baloncesto - ANB Rising Stars",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(videos_router, prefix="/api/videos", tags=["Videos"])
app.include_router(public_router, prefix="/api/public", tags=["Public"])

@app.get("/")
async def root():
    return {"message": "ANB Video Manage API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
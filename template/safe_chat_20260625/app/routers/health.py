from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": f"{settings.PROJECT_NAME} is running",
        "version": settings.VERSION
    }

@router.get("/")
async def root():
    return {"message": "Welcome to Agent API. Use /agent/chat for interaction."}

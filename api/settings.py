# FastAPI backend for user settings and preferences
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from sqlalchemy.orm import Session
from model.db import SessionLocal, UserSettings, User, init_db
from api.auth import get_current_user

router = APIRouter()

init_db()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Settings(BaseModel):
    email: EmailStr
    theme: str = Field("light", min_length=2, max_length=16, pattern=r"^(light|dark)$")
    language: str = Field("en", min_length=2, max_length=8, pattern=r"^[a-z]{2,8}$")
    notifications: bool = True
    mapProvider: str = Field("google", min_length=2, max_length=32)
    voiceMode: Optional[str] = Field(None, min_length=2, max_length=32)

@router.get("/settings")
def get_settings(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        return Settings(email=current_user.email).dict()
    return {
        "email": current_user.email,
        "theme": settings.theme,
        "language": settings.language,
        "notifications": settings.notifications,
        "mapProvider": settings.mapProvider,
        "voiceMode": settings.voiceMode
    }

@router.post("/settings")
def set_settings(settings: Settings, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not db_settings:
        db_settings = UserSettings(user_id=current_user.id)
        db.add(db_settings)
    db_settings.theme = settings.theme
    db_settings.language = settings.language
    db_settings.notifications = settings.notifications
    db_settings.mapProvider = settings.mapProvider
    db_settings.voiceMode = settings.voiceMode
    db.commit()
    return {"ok": True}

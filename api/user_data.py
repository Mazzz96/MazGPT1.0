# FastAPI backend for GDPR-compliant user data management
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import List
from sqlalchemy.orm import Session
from model.db import SessionLocal, User, ChatMemory, init_db
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

class ChatExport(BaseModel):
    email: EmailStr
    chats: List[dict] = Field(..., min_length=0, max_length=100)

@router.get("/export-data")
def export_data(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    chats = db.query(ChatMemory).filter(ChatMemory.user_id == current_user.id).all()
    return {"chats": [{"project_id": c.project_id, "messages": c.messages} for c in chats]}

@router.post("/import-data")
def import_data(export: ChatExport, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    for chat in export.chats:
        project_id = chat.get("project_id", "default")
        if not isinstance(project_id, str) or not 1 <= len(project_id) <= 64:
            raise HTTPException(status_code=400, detail="Invalid project_id in import")
        messages = chat.get("messages", [])
        if not isinstance(messages, list) or len(messages) > 1000:
            raise HTTPException(status_code=400, detail="Invalid messages in import")
        db.add(ChatMemory(user_id=current_user.id, project_id=project_id, messages=messages))
    db.commit()
    return {"ok": True}

@router.post("/delete-data")
def delete_data(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(ChatMemory).filter(ChatMemory.user_id == current_user.id).delete()
    db.commit()
    return {"ok": True}

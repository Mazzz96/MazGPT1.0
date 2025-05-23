# api/chat.py
# Chat API endpoints for MazGPT
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import constr, BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from model.db import SessionLocal, User, ChatMemory, ChatMessage, Project, init_db
from api.auth import get_current_user
from model.semantic_memory import SemanticMemory
import logging
from sqlalchemy import or_

router = APIRouter()
init_db()
semantic_memory = SemanticMemory()

# --- Pydantic models ---
class ChatSendRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")
    message: str = Field(..., min_length=1, max_length=2000)

class ChatMessage(BaseModel):
    sender: str = Field(..., min_length=1, max_length=16, pattern=r"^(user|ai)$")
    text: str = Field(..., min_length=1, max_length=2000)
    timestamp: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")
    messages: List[ChatMessage]

class ChatSearchResponse(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")
    results: List[ChatMessage]
    total: int
    offset: int
    limit: int
    semantic: bool

# --- POST /chat/send ---
@router.post("/chat/send")
def send_chat(req: ChatSendRequest, current_user=Depends(get_current_user), db: Session = Depends(SessionLocal)):
    # Validate project ownership
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    # Add user message
    user_msg = ChatMessage(
        project_id=project.id,
        user_id=current_user.id,
        sender="user",
        content=req.message,
        version=1
    )
    db.add(user_msg)
    # --- AI response (stub, replace with real LLM call) ---
    ai_reply = f"MazGPT: You said '{req.message}' (project: {req.project_id})"
    ai_msg = ChatMessage(
        project_id=project.id,
        user_id=current_user.id,
        sender="ai",
        content=ai_reply,
        version=1
    )
    db.add(ai_msg)
    db.commit()
    logging.info(f"User {current_user.email} sent message to project {req.project_id}")
    return {"reply": ai_reply}

# --- GET /chat/history ---
@router.get("/chat/history", response_model=ChatHistoryResponse)
def get_chat_history(
    project_id: str = Query(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$"),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user), db: Session = Depends(SessionLocal)):
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        return {"project_id": project_id, "messages": []}
    msgs = db.query(ChatMessage).filter(ChatMessage.project_id == project.id, ChatMessage.user_id == current_user.id).order_by(ChatMessage.created_at.asc()).limit(limit).all()
    return {
        "project_id": project_id,
        "messages": [ChatMessage(sender=m.sender, text=m.content, timestamp=m.created_at.isoformat()) for m in msgs]
    }

# --- Optionally: GET /chat/search (semantic/keyword search) ---
# TODO: Implement semantic/keyword search using ChromaDB or similar
# --- GET /chat/search ---
@router.get("/chat/search", response_model=ChatSearchResponse)
def search_chat(
    q: str = Query(..., min_length=1, max_length=200),
    project_id: str = Query(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$"),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    semantic: bool = Query(False),
    current_user=Depends(get_current_user),
    db: Session = Depends(SessionLocal)
):
    # Input sanitization
    query_str = q.strip()
    if not query_str:
        raise HTTPException(status_code=400, detail="Empty query")
    # Validate project ownership
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    results = []
    total = 0
    if semantic:
        # Semantic search via ChromaDB
        sem_results = semantic_memory.query(query_str, n_results=limit+offset, project_id=project_id)
        total = len(sem_results)
        sem_results = sem_results[offset:offset+limit]
        results = [ChatMessage(sender=m[1].get('user','user'), text=m[0], timestamp=None) for m in sem_results]
    else:
        # Full-text search (simple LIKE for now, can use FTS5 if available)
        q_filter = f"%{query_str.lower()}%"
        query = db.query(ChatMessage).filter(
            ChatMessage.project_id == project.id,
            ChatMessage.user_id == current_user.id,
            or_(ChatMessage.content.ilike(q_filter))
        ).order_by(ChatMessage.created_at.desc())
        total = query.count()
        msgs = query.offset(offset).limit(limit).all()
        results = [ChatMessage(sender=m.sender, text=m.content, timestamp=m.created_at.isoformat()) for m in msgs]
    logging.info(f"User {current_user.email} searched chat in project {project_id} (semantic={semantic}) q='{query_str}'")
    return ChatSearchResponse(
        project_id=project_id,
        results=results,
        total=total,
        offset=offset,
        limit=limit,
        semantic=semantic
    )

# api/project.py
# Project management API endpoints for MazGPT
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List
from sqlalchemy.orm import Session
from model.db import SessionLocal, User, ChatMemory, Project, init_db
from api.auth import get_current_user
import logging
from datetime import datetime, timedelta, timezone

router = APIRouter()
init_db()

# --- Pydantic models ---
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")

class ProjectRenameRequest(BaseModel):
    old_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")
    new_name: str = Field(..., min_length=1, max_length=64)
    new_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")

class ProjectArchiveRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")

class ProjectDeleteRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")
    confirm: bool

class ProjectInfo(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")
    name: str = Field(..., min_length=1, max_length=64)
    archived: bool = False

# --- POST /project/create ---
@router.post("/project/create")
def create_project(req: ProjectCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(SessionLocal)):
    # Validate unique name/id for user
    existing = db.query(Project).filter(Project.user_id == current_user.id, Project.name == req.name).first()
    if req.id == "default" or existing:
        raise HTTPException(status_code=400, detail="Project ID or name already exists or reserved.")
    project = Project(user_id=current_user.id, name=req.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    logging.info(f"User {current_user.email} created project {project.id}")
    return {"ok": True, "id": project.id, "name": project.name}

# --- GET /project/list ---
@router.get("/project/list", response_model=List[ProjectInfo])
def list_projects(current_user=Depends(get_current_user), db: Session = Depends(SessionLocal)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return [ProjectInfo(id=p.id, name=p.name, archived=p.archived) for p in projects]

# --- POST /project/rename ---
@router.post("/project/rename")
def rename_project(req: ProjectRenameRequest, current_user=Depends(get_current_user), db: Session = Depends(SessionLocal)):
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == req.old_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    # Check for name conflict
    if db.query(Project).filter(Project.user_id == current_user.id, Project.name == req.new_name, Project.id != req.old_id).first():
        raise HTTPException(status_code=400, detail="New project name already exists.")
    project.name = req.new_name
    db.commit()
    logging.info(f"User {current_user.email} renamed project {req.old_id} to {req.new_name}")
    return {"ok": True, "id": project.id, "name": project.name}

# --- POST /project/archive ---
@router.post("/project/archive")
def archive_project(req: ProjectArchiveRequest, current_user=Depends(get_current_user), db: Session = Depends(SessionLocal)):
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == req.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    project.archived = True
    project.archived_at = datetime.now(timezone.utc)
    db.commit()
    logging.info(f"User {current_user.email} archived project {req.id}")
    return {"ok": True}

# --- DELETE /project/delete ---
@router.delete("/project/delete")
def delete_project(req: ProjectDeleteRequest, current_user=Depends(get_current_user), db: Session = Depends(SessionLocal)):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required.")
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == req.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    db.query(ChatMemory).filter(ChatMemory.user_id == current_user.id, ChatMemory.project_id == project.id).delete()
    db.delete(project)
    db.commit()
    logging.info(f"User {current_user.email} deleted project {req.id}")
    return {"ok": True}

# Database models and session for MazGPT (SQLite, SQLAlchemy)
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    tier = Column(String, default="Free")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Two-Factor Authentication (2FA) fields
    twofa_enabled = Column(Boolean, default=False)
    twofa_type = Column(String, nullable=True)  # 'totp' or 'email'
    twofa_secret_enc = Column(String, nullable=True)  # Encrypted TOTP secret
    twofa_email_code = Column(String, nullable=True)  # Last sent email code
    twofa_email_code_expiry = Column(DateTime, nullable=True)  # Expiry for email code

class UserSettings(Base):
    __tablename__ = 'user_settings'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    theme = Column(String, default="light")
    language = Column(String, default="en")
    notifications = Column(Boolean, default=True)
    mapProvider = Column(String, default="google")
    voiceMode = Column(String, nullable=True)

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # removed index=True
    name = Column(String, nullable=False)
    archived = Column(Boolean, default=False)  # removed index=True
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # removed index=True
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship('User')
    chat_memories = relationship('ChatMemory', back_populates='project')

    __table_args__ = (
        Index('ix_projects_user_id', 'user_id'),
        Index('ix_projects_created_at', 'created_at'),
    )

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)  # removed index=True
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # removed index=True
    sender = Column(String, nullable=False)  # 'user' or 'ai'
    content = Column(String, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # removed index=True
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship('Project')
    user = relationship('User')

    __table_args__ = (
        Index('ix_chat_messages_user_id', 'user_id'),
        Index('ix_chat_messages_project_id', 'project_id'),
        Index('ix_chat_messages_created_at', 'created_at'),
    )

class ChatMemory(Base):
    __tablename__ = 'chat_memory'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)  # removed index=True
    messages = Column(JSON, nullable=False)  # List of message dicts (legacy, for migration)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship('User')
    project = relationship('Project', back_populates='chat_memories')

engine = create_engine("sqlite:///mazgpt.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if not exist
def init_db():
    Base.metadata.create_all(bind=engine)

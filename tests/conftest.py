import pytest
from fastapi.testclient import TestClient
from api.__init__ import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.db import Base, SessionLocal
import model.db
import os

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Patch SessionLocal globally for tests
model.db.engine = engine
model.db.SessionLocal = TestingSessionLocal

# Create all tables before tests
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db_session):
    os.environ["TESTING"] = "1"
    app.dependency_overrides[model.db.SessionLocal] = lambda: db_session
    with TestClient(app) as c:
        # --- CSRF token setup ---
        resp = c.get("/ping")
        csrf_token = None
        for cookie in c.cookies:
            if cookie == "mazgpt-csrf":
                csrf_token = c.cookies[cookie]
                break
        # Patch request methods to always add x-csrf-token for state-changing requests
        orig_request = c.request
        def csrf_request(method, url, *args, **kwargs):
            headers = kwargs.pop("headers", {}) or {}
            if method.upper() in ("POST", "PUT", "DELETE", "PATCH") and csrf_token:
                headers["x-csrf-token"] = csrf_token
            kwargs["headers"] = headers
            return orig_request(method, url, *args, **kwargs)
        c.request = csrf_request
        yield c
    app.dependency_overrides = {}

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.db import Base, get_db
from backend.app.main import app
from backend.app import models

@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    def override_db():
        db = TestingSession()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr("backend.app.main.UPLOAD_DIR", tmp_path / "uploads")
    (tmp_path / "uploads").mkdir()
    with TestClient(app) as test_client:
        test_client.demo_session = TestingSession
        yield test_client
    app.dependency_overrides.clear(); Base.metadata.drop_all(engine); engine.dispose()

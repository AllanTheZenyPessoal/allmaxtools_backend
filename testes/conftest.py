"""Configuração mínima de testes para user/token/health."""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
os.environ["TESTING"] = "1"

from main import app
from database import db_models
from database.db_models import Base
from dependencies import get_db
from endpoint.user import get_password_hash
from token_utils.apikey_generator import create_access_token


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def superadmin_user(test_db):
    user = db_models.User(
        username="superadmin",
        email="superadmin@gmail.com",
        password=get_password_hash("123123123"),
        phone="11999999999",
        role="superadmin",
        company_id=None,
        active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def mock_token(superadmin_user):
    return create_access_token(
        email=superadmin_user.email,
        username=superadmin_user.username,
        id_user=superadmin_user.id_user,
        role=superadmin_user.role,
        company_id=superadmin_user.company_id,
    )


@pytest.fixture
def auth_headers(mock_token):
    return {"Authorization": f"Bearer {mock_token}"}


@pytest.fixture
def user_payload():
    return {
        "username": "novousuario",
        "email": "novo@teste.com",
        "password": "senha123456",
        "phone": "11966666666",
        "role": "user",
    }

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import sessao
from app.main import app


@pytest.fixture
def cliente():
    """Cliente de teste com SQLite em memória, sem tocar no banco real do .env."""
    eng = create_engine("sqlite://")
    fabrica = sessionmaker(bind=eng)

    def sessao_teste():
        with fabrica() as s:
            yield s

    app.dependency_overrides[sessao] = sessao_teste
    yield TestClient(app)
    app.dependency_overrides.clear()

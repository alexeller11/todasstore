"""Configura fixtures de teste compartilhadas.

Usa um Flask app + SQLite em memória para que os testes sejam rápidos e
isolados do ambiente do desenvolvedor."""
import os
import tempfile

import pytest

# força SQLite em arquivo temporário (migrations do Alembic e relacionamentos
# não funcionam em pure-memory shared-cache no Windows em alguns motores)
os.environ.setdefault("DATABASE_URL", "")

from app import create_app
from app.extensions import db as _db


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path.as_posix()}",
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret",
    )

    with app.app_context():
        _db.create_all()

    yield app

    with app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    from app.extensions import db as _db
    with app.app_context():
        yield _db

"""Testes para a rodada de melhorias: rate limit nas gerações por IA,
autenticação 'fail-closed' da rota /admin/sync-schema, e filtro por tipo
no banco de ideias."""
import os

import pytest

from app import create_app
from config import Config


class ConfigSemCSRF(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"


@pytest.fixture()
def client2():
    application = create_app(ConfigSemCSRF)
    with application.app_context():
        yield application.test_client()


def test_gerar_semana_bloqueia_apos_limite(client2):
    from app.services import planner_service

    with client2.application.app_context():
        mes = planner_service.obter_ou_criar_mes(2026, 7)
        semana_id = mes.semanas[0].id

    respostas = []
    for _ in range(7):
        resp = client2.post(f"/planejamento/semana/{semana_id}/gerar", follow_redirects=True)
        respostas.append("Muitos pedidos" in resp.data.decode())

    # as 5 primeiras não devem estar bloqueadas pelo limitador; a partir da 6ª, sim
    assert respostas[:5] == [False] * 5
    assert respostas[5] is True and respostas[6] is True


def test_admin_sync_schema_bloqueia_em_producao_sem_token(client2, monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.delenv("ADMIN_SYNC_TOKEN", raising=False)
    resp = client2.get("/admin/sync-schema")
    assert resp.status_code == 403


def test_admin_sync_schema_permite_em_dev_sem_token(client2, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.delenv("ADMIN_SYNC_TOKEN", raising=False)
    resp = client2.get("/admin/sync-schema")
    assert resp.status_code == 200


def test_admin_sync_schema_exige_token_correto_em_producao(client2, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("ADMIN_SYNC_TOKEN", "segredo123")
    resp = client2.get("/admin/sync-schema?token=errado")
    assert resp.status_code == 403
    resp = client2.get("/admin/sync-schema?token=segredo123")
    assert resp.status_code == 200


def test_banco_ideias_filtra_por_tipo(client2):
    from app.models import Ideia
    from app.extensions import db

    with client2.application.app_context():
        db.session.add(Ideia(titulo="Ideia Story", tipo="story", conteudo="x", origem="manual"))
        db.session.add(Ideia(titulo="Ideia Reels", tipo="reels", conteudo="y", origem="manual"))
        db.session.commit()

    resp = client2.get("/ideias/?tipo=story")
    assert b"Ideia Story" in resp.data
    assert b"Ideia Reels" not in resp.data

    resp = client2.get("/ideias/?tipo=reels")
    assert b"Ideia Reels" in resp.data
    assert b"Ideia Story" not in resp.data

    resp = client2.get("/ideias/")
    assert b"Ideia Story" in resp.data and b"Ideia Reels" in resp.data

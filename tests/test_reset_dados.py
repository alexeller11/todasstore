"""Testes para /admin/reset-dados: apaga todos os dados (loja, planejamento,
banco de ideias, concorrentes) preservando o esquema, para entregar o app
"zerado" para um cliente novo.

Usa um arquivo SQLite temporario (em vez de ":memory:") porque a rota chama
db.engine.dispose() ao final (necessario em producao para evitar conexoes
com transacao abortada) - e um banco ":memory:" perde o esquema inteiro
quando a conexao e fechada, o que so acontece nesse modo de teste, nunca
com SQLite em arquivo ou PostgreSQL (producao)."""
import os
import tempfile

import pytest

from app import create_app
from config import Config


@pytest.fixture()
def client_reset(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("ADMIN_SYNC_TOKEN", "segredo123")

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    class ConfigComCSRF(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        WTF_CSRF_ENABLED = True
        SECRET_KEY = "test-secret"

    application = create_app(ConfigComCSRF)
    with application.app_context():
        yield application.test_client()

    os.remove(db_path)


def _povoar_dados(app):
    from app.models import Loja, Ideia, Concorrente
    from app.services import planner_service
    from app.extensions import db

    with app.app_context():
        db.session.add(Loja(nome="Loja da Cliente"))
        db.session.add(Ideia(titulo="Ideia teste", tipo="story", conteudo="x", origem="manual"))
        db.session.add(Concorrente(instagram="concorrente_x"))
        planner_service.obter_ou_criar_mes(2026, 7)
        db.session.commit()


def test_reset_dados_exige_token(client_reset):
    resp = client_reset.get("/admin/reset-dados")
    assert resp.status_code == 403


def test_reset_dados_get_mostra_confirmacao_sem_apagar_nada(client_reset):
    _povoar_dados(client_reset.application)

    resp = client_reset.get("/admin/reset-dados?token=segredo123")
    assert resp.status_code == 200
    assert b"Sim, apagar tudo" in resp.data

    from app.models import Loja
    with client_reset.application.app_context():
        assert Loja.query.count() == 1  # GET nao deve apagar nada


def test_reset_dados_post_sem_confirmar_e_bloqueado(client_reset):
    _povoar_dados(client_reset.application)
    resp = client_reset.post("/admin/reset-dados?token=segredo123", data={})
    assert resp.status_code == 400

    from app.models import Loja
    with client_reset.application.app_context():
        assert Loja.query.count() == 1


def test_reset_dados_post_com_confirmacao_apaga_tudo(client_reset):
    _povoar_dados(client_reset.application)

    resp = client_reset.post(
        "/admin/reset-dados?token=segredo123", data={"confirmar": "RESETAR"}
    )
    assert resp.status_code == 200
    corpo = resp.get_json()
    assert corpo["ok"] is True

    from app.models import Loja, Ideia, Concorrente, Mes, Dia
    with client_reset.application.app_context():
        assert Loja.query.count() == 0
        assert Ideia.query.count() == 0
        assert Concorrente.query.count() == 0
        assert Mes.query.count() == 0
        assert Dia.query.count() == 0

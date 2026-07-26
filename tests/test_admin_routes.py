"""Tests for the administrative routes defined in ``app.routes.admin``.
The tests run against a Flask test client with ``FLASK_ENV=development``
so that the admin token authentication is bypassed.
"""
import os
import pytest

from app import create_app

@pytest.fixture(scope="function")
def client():
    # Ensure development mode – token auth is disabled
    os.environ["FLASK_ENV"] = "development"
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_sync_schema_success(client):
    resp = client.get("/admin/sync-schema")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert "relatorio" in data

def test_reset_dados_get_html(client):
    resp = client.get("/admin/reset-dados")
    assert resp.status_code == 200
    # the rendered template contains the confirmation headline
    assert b"Resetar TODOS os dados?" in resp.data

def test_reset_dados_post_success(client):
    # In development the token check is skipped, we only need the confirm param
    resp = client.post("/admin/reset-dados", data={"confirmar": "RESETAR"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["mensagem"] == "Dados resetados. Acesse o app normalmente - ele vai pedir o onboarding do zero."

def test_reset_dados_missing_confirm(client):
    resp = client.post("/admin/reset-dados", data={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["ok"] is False
    assert data["erro"] == "confirmacao ausente"

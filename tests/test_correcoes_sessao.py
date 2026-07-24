"""Testes para as correções/adições desta sessão:
- bug do CSRF ausente no fetch de alternar checklist (estava quebrado em produção)
- validação de extensão/tamanho no upload de logo
- resumo da semana pronto pra WhatsApp
"""
import io
import re

import pytest

from app import create_app
from config import Config


class ConfigComCSRF(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = True
    SECRET_KEY = "test-secret"


@pytest.fixture()
def client_com_csrf():
    application = create_app(ConfigComCSRF)
    with application.app_context():
        yield application.test_client()


def _pega_token(html):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else None


def test_checklist_toggle_precisa_do_header_csrf(client_com_csrf, app_context_helper=None):
    from app.services import planner_service
    from app.extensions import db

    with client_com_csrf.application.app_context():
        mes = planner_service.obter_ou_criar_mes(2026, 7)
        dia = mes.semanas[0].dias[0]
        from app.services.checklist_service import adicionar_item
        item = adicionar_item(dia.id, "Item de teste")
        item_id = item.id

    # sem header X-CSRFToken -> deve falhar (era o bug real em produção)
    resp = client_com_csrf.post(f"/planejamento/checklist/{item_id}/alternar")
    assert resp.status_code == 400

    # com o header (como o app.js corrigido agora envia) -> deve funcionar
    html = client_com_csrf.get("/configuracoes/").data.decode()
    token = _pega_token(html)
    resp = client_com_csrf.post(
        f"/planejamento/checklist/{item_id}/alternar",
        headers={"X-CSRFToken": token},
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_upload_logo_recusa_extensao_nao_permitida(client_com_csrf):
    html = client_com_csrf.get("/configuracoes/").data.decode()
    token = _pega_token(html)
    arquivo_ruim = (io.BytesIO(b"conteudo qualquer"), "arquivo.exe")
    resp = client_com_csrf.post(
        "/configuracoes/",
        data={"nome": "Loja X", "csrf_token": token, "logo_file": arquivo_ruim},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "não suportado".encode() in resp.data or "n\u00e3o suportado".encode("utf-8") in resp.data


def test_upload_logo_aceita_png_valido(client_com_csrf):
    from PIL import Image

    html = client_com_csrf.get("/configuracoes/").data.decode()
    token = _pega_token(html)

    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), (255, 0, 0)).save(buffer, format="PNG")
    buffer.seek(0)

    resp = client_com_csrf.post(
        "/configuracoes/",
        data={"nome": "Loja Y", "csrf_token": token, "logo_file": (buffer, "logo.png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 302

    from app.models import Loja
    with client_com_csrf.application.app_context():
        loja = Loja.query.first()
        assert loja.logo_url and "uploads" in loja.logo_url


def test_resumo_whatsapp_da_semana_contem_conteudo_gerado(client_com_csrf):
    from app.services import planner_service
    from app.extensions import db

    with client_com_csrf.application.app_context():
        mes = planner_service.obter_ou_criar_mes(2026, 7)
        semana = mes.semanas[0]
        semana.dias[0].ideia_story = "Mostrar bastidor da loja"
        db.session.commit()
        semana_id = semana.id

    resp = client_com_csrf.get(f"/planejamento/semana/{semana_id}")
    assert resp.status_code == 200
    assert "Mostrar bastidor da loja".encode() in resp.data

"""Testes para a rodada de melhorias de intuitividade/didatismo:
onboarding em etapas, sugestão ativa no dashboard, item de menu de
planejamento, tooltips de termos técnicos e página de ajuda."""
import pytest

from app import create_app
from config import Config


class ConfigSemCSRF(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"


@pytest.fixture()
def client3():
    application = create_app(ConfigSemCSRF)
    with application.app_context():
        yield application.test_client()


def test_onboarding_renderiza_como_wizard_de_4_passos(client3):
    resp = client3.get("/bem-vinda")
    assert resp.status_code == 200
    assert b"Passo 1 de 4" in resp.data
    assert b"btn-proximo" in resp.data or b'id="btn-proximo"' in resp.data


def test_onboarding_post_completo_cria_loja(client3):
    resp = client3.post(
        "/bem-vinda",
        data={
            "nome": "Loja da Cliente",
            "cidade": "Linhares",
            "instagram": "@loja",
            "estilo": "casual",
            "publico": "mulheres 20-35",
            "faixa_preco": "R$ 80-200",
            "produtos": "vestidos",
            "tom_de_voz": "descontraida",
            "objetivos": "vender mais",
            "diferenciais": "atendimento no whatsapp",
            "dores_do_publico": "nao sabe combinar roupa",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    from app.models import Loja
    with client3.application.app_context():
        loja = Loja.query.first()
        assert loja is not None
        assert loja.nome == "Loja da Cliente"
        assert loja.onboarding_concluido is True


def test_dashboard_sugere_gerar_planejamento_quando_semana_vazia(client3):
    from app.models import Loja
    from app.extensions import db
    from app.services import planner_service
    from datetime import date

    with client3.application.app_context():
        db.session.add(Loja(nome="Loja Teste", onboarding_concluido=True))
        db.session.commit()
        hoje = date.today()
        planner_service.obter_ou_criar_mes(hoje.year, hoje.month)

    resp = client3.get("/")
    assert resp.status_code == 200
    assert "ainda está em branco".encode() in resp.data


def test_menu_inferior_tem_link_de_planejamento(client3):
    from app.models import Loja
    from app.extensions import db

    with client3.application.app_context():
        db.session.add(Loja(nome="Loja Teste", onboarding_concluido=True))
        db.session.commit()

    resp = client3.get("/")
    assert b"Planejamento" in resp.data
    assert b"bi-calendar3" in resp.data


def test_pagina_de_ajuda_carrega(client3):
    resp = client3.get("/configuracoes/ajuda")
    assert resp.status_code == 200
    assert "Como funciona".encode() in resp.data
    assert "CTA".encode() in resp.data


def test_dia_html_tem_tooltips_explicativos(client3):
    from app.services import planner_service
    from datetime import date

    with client3.application.app_context():
        hoje = date.today()
        mes = planner_service.obter_ou_criar_mes(hoje.year, hoje.month)
        dia_id = mes.semanas[0].dias[0].id

    resp = client3.get(f"/planejamento/dia/{dia_id}")
    assert resp.status_code == 200
    assert b"bi-question-circle" in resp.data
    assert "24h no ar".encode() in resp.data


def test_botoes_de_gerar_ideia_tem_classe_de_loading(client3):
    from app.services import planner_service
    from datetime import date

    with client3.application.app_context():
        hoje = date.today()
        mes = planner_service.obter_ou_criar_mes(hoje.year, hoje.month)
        dia_id = mes.semanas[0].dias[0].id

    resp = client3.get(f"/planejamento/dia/{dia_id}")
    assert resp.data.count(b"form-ia") >= 3  # story, reels, feed


def test_confirmacao_antes_de_excluir_ideia(client3):
    from app.models import Ideia
    from app.extensions import db

    with client3.application.app_context():
        db.session.add(Ideia(titulo="Teste", tipo="story", conteudo="x", origem="manual"))
        db.session.commit()

    resp = client3.get("/ideias/")
    assert b"onsubmit=\"return confirm(" in resp.data

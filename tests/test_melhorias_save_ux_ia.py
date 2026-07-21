"""Testes das frentes 1 e 2 desta rodada de melhorias:
- bug do checklist reset (selo volta pra False ao desmarcar)
- 'salvar do dia' cria Ideia com origem=ia
- versões anteriores sao preservadas ao regenerar
"""
from datetime import date

from app.extensions import db
from app.models import Loja, Mes, Semana, Dia, ChecklistItem, Ideia, VersaoConteudo
from app.services import checklist_service


def _seed_dia(app):
    loja = Loja(nome="Loja Teste", onboarding_concluido=True)
    db.session.add(loja)
    mes = Mes(ano=2026, numero=7, nome="Julho")
    db.session.add(mes)
    db.session.flush()
    semana = Semana(
        mes_id=mes.id, numero=1,
        data_inicio=date(2026, 7, 6), data_fim=date(2026, 7, 12),
    )
    db.session.add(semana)
    db.session.flush()
    dia = Dia(semana_id=semana.id, data=date(2026, 7, 6), dia_semana="segunda")
    db.session.add(dia)
    db.session.commit()
    return dia


def test_alternar_checklist_reseta_selo_ao_desmarcar(app):
    with app.app_context():
        dia = _seed_dia(app)
        item = ChecklistItem(dia_id=dia.id, texto="Publicar Story", ordem=0)
        db.session.add(item)
        db.session.commit()

        # marcar -> dia.story_feito vira True
        checklist_service.alternar_item(item.id)
        assert item.concluido is True
        assert item.dia.story_feito is True, "marcar deveria acender o selo"

        # desmarcar -> dia.story_feito volta a False (bug corrigido)
        checklist_service.alternar_item(item.id)
        assert item.concluido is False
        assert item.dia.story_feito is False, \
            "desmarcar deveria apagar o selo (antes ficava preso em True)"


def test_selo_mantem_ligado_enquanto_ha_outro_item_marcado(app):
    with app.app_context():
        dia = _seed_dia(app)
        i1 = ChecklistItem(dia_id=dia.id, texto="Publicar Story", ordem=0)
        i2 = ChecklistItem(dia_id=dia.id, texto="Repostar Story", ordem=1)
        db.session.add_all([i1, i2])
        db.session.commit()

        checklist_service.alternar_item(i1.id)
        checklist_service.alternar_item(i2.id)
        assert dia.story_feito is True

        # desmarca i1, mas i2 ainda esta marcado -> selo continua
        checklist_service.alternar_item(i1.id)
        assert dia.story_feito is True, \
            "com i2 ainda marcado, o selo nao deveria apagar"

        # desmarca i2 (ultimo) -> agora sim apaga
        checklist_service.alternar_item(i2.id)
        assert dia.story_feito is False


def test_salvar_do_dia_cria_ideia_origem_ia(app):
    with app.app_context():
        dia = _seed_dia(app)
        dia.ideia_story = "Story mostrando arara com vestidos floridos"
        dia.legenda = "Cansada de chegar no rails e nao ter o que vestir?..."
        dia.cta = "Chama no WhatsApp"
        db.session.commit()

        client = app.test_client()
        resp = client.post(f"/ideias/salvar-do-dia/{dia.id}/story")

        assert resp.status_code == 302
        ideia = Ideia.query.filter_by(origem="ia").first()
        assert ideia is not None, "deveria criar Ideia com origem=ia"
        assert ideia.tipo == "story"
        assert "arara com vestidos floridos" in ideia.conteudo
        assert ideia.legenda.startswith("Cansada")
        assert ideia.cta == "Chama no WhatsApp"
        assert "Segunda" in ideia.titulo
        assert "06/07/2026" in ideia.titulo


def test_salvar_do_dia_sem_conteudo_nao_cria_ideia(app):
    with app.app_context():
        dia = _seed_dia(app)
        # dia.ideia_story vazio de proposito
        client = app.test_client()
        resp = client.post(f"/ideias/salvar-do-dia/{dia.id}/story")

        assert resp.status_code == 302
        assert Ideia.query.count() == 0


def test_preservar_versao_nao_duplica_identicas(app):
    from app.services.planner_service import _preservar_versao_se_existir
    with app.app_context():
        dia = _seed_dia(app)
        dia.ideia_story = "ideia A"
        dia.legenda = "legenda A"
        db.session.commit()

        _preservar_versao_se_existir(dia, apenas_tipo="story")
        db.session.commit()
        assert VersaoConteudo.query.filter_by(
            dia_id=dia.id, tipo="story"
        ).count() == 1

        # chamar de novo sem mudar nada -> nao duplica
        _preservar_versao_se_existir(dia, apenas_tipo="story")
        db.session.commit()
        assert VersaoConteudo.query.filter_by(
            dia_id=dia.id, tipo="story"
        ).count() == 1

        # mudar -> cria segunda versao
        dia.ideia_story = "ideia B"
        _preservar_versao_se_existir(dia, apenas_tipo="story")
        db.session.commit()
        total = VersaoConteudo.query.filter_by(
            dia_id=dia.id, tipo="story"
        ).count()
        assert total == 2

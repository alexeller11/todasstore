from app.extensions import db
from app.models import ChecklistItem
from flask import current_app


def criar_checklist_padrao(dia_id, salvar=True):
    itens_padrao = current_app.config.get("CHECKLIST_PADRAO", [])
    for ordem, texto in enumerate(itens_padrao):
        item = ChecklistItem(dia_id=dia_id, texto=texto, ordem=ordem)
        db.session.add(item)
    if salvar:
        db.session.commit()


def alternar_item(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    item.concluido = not item.concluido
    db.session.commit()

    # Atualiza sinalizadores do dia (story/post feitos) com base em palavras-chave simples
    dia = item.dia
    texto_lower = item.texto.lower()
    if "story" in texto_lower and item.concluido:
        dia.story_feito = True
    if ("feed" in texto_lower or "reels" in texto_lower) and item.concluido:
        dia.post_feito = True
    db.session.commit()
    return item


def adicionar_item(dia_id, texto):
    ultimo = ChecklistItem.query.filter_by(dia_id=dia_id).count()
    item = ChecklistItem(dia_id=dia_id, texto=texto, ordem=ultimo)
    db.session.add(item)
    db.session.commit()
    return item


def editar_item(item_id, novo_texto):
    item = ChecklistItem.query.get_or_404(item_id)
    item.texto = novo_texto
    db.session.commit()
    return item


def remover_item(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

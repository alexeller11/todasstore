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


def _item_indica(titulo, palavras_chave):
    """True se o item (pelo texto) representa um story, post, feed ou reels."""
    texto_lower = titulo.lower()
    return any(p in texto_lower for p in palavras_chave)


def _recalcular_selos_do_dia(dia):
    """Recomputa story_feito e post_feito analisando TODOS os itens do dia,
    de forma determinística. Substitui a lógica antiga que só setava True
    e nunca resetava False ao desmarcar — o que deixava o selo "preso" em verde
    e dava a impressão de que o checklist "não estava salvando"."""
    itens = list(dia.checklist_items)
    dia.story_feito = any(
        i.concluido and _item_indica(i.texto, ["story"]) for i in itens
    )
    dia.post_feito = any(
        i.concluido and _item_indica(i.texto, ["feed", "reels", "post"]) for i in itens
    )


def alternar_item(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    item.concluido = not item.concluido
    db.session.commit()

    _recalcular_selos_do_dia(item.dia)
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

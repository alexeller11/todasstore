from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash

from app.models import Mes, Semana, Dia
from app.services import planner_service, checklist_service, analytics_service

bp = Blueprint("planejamento", __name__, url_prefix="/planejamento")


@bp.route("/mes/<int:ano>/<int:numero>")
def ver_mes(ano, numero):
    mes = planner_service.obter_ou_criar_mes(ano, numero)
    stats = analytics_service.progresso_mes(mes.id)
    return render_template("mes.html", mes=mes, stats=stats)


@bp.route("/semana/<int:semana_id>")
def ver_semana(semana_id):
    semana = Semana.query.get_or_404(semana_id)
    stats = analytics_service.progresso_semana(semana_id)
    return render_template("semana.html", semana=semana, stats=stats)


@bp.route("/semana/<int:semana_id>/promocao", methods=["POST"])
def salvar_promocao(semana_id):
    from app.extensions import db
    semana = Semana.query.get_or_404(semana_id)
    semana.promocao = request.form.get("promocao", "").strip() or None
    db.session.commit()
    flash("Promoção da semana salva! 🎉", "success")
    return redirect(url_for("planejamento.ver_semana", semana_id=semana_id))


@bp.route("/semana/<int:semana_id>/gerar", methods=["POST"])
def gerar_semana(semana_id):
    try:
        planner_service.gerar_planejamento_semana(semana_id)
        flash("Planejamento da semana criado com sucesso! ✨", "success")
    except Exception as e:
        flash(f"Não consegui gerar agora: {e}", "danger")
    return redirect(url_for("planejamento.ver_semana", semana_id=semana_id))


@bp.route("/dia/<int:dia_id>")
def ver_dia(dia_id):
    dia = Dia.query.get_or_404(dia_id)
    return render_template("dia.html", dia=dia)


@bp.route("/dia/<int:dia_id>/nova-ideia/<tipo>", methods=["POST"])
def nova_ideia(dia_id, tipo):
    try:
        planner_service.gerar_nova_ideia_dia(dia_id, tipo)
        flash("Nova ideia gerada! 🔄", "success")
    except Exception as e:
        flash(f"Não consegui gerar agora: {e}", "danger")
    return redirect(url_for("planejamento.ver_dia", dia_id=dia_id))


@bp.route("/dia/<int:dia_id>/editar", methods=["POST"])
def editar_dia(dia_id):
    from app.extensions import db
    dia = Dia.query.get_or_404(dia_id)

    dia.ideia_story = request.form.get("ideia_story") or dia.ideia_story
    dia.ideia_reels = request.form.get("ideia_reels") or dia.ideia_reels
    dia.ideia_feed = request.form.get("ideia_feed") or dia.ideia_feed
    dia.legenda = request.form.get("legenda") or dia.legenda
    dia.cta = request.form.get("cta") or dia.cta

    db.session.commit()
    flash("Conteúdo do dia atualizado!", "success")
    return redirect(url_for("planejamento.ver_dia", dia_id=dia_id))


# --- checklist (usado via fetch/JS na tela do dia) ---

@bp.route("/checklist/<int:item_id>/alternar", methods=["POST"])
def alternar_checklist(item_id):
    item = checklist_service.alternar_item(item_id)
    return jsonify({"ok": True, "concluido": item.concluido})


@bp.route("/checklist/dia/<int:dia_id>/adicionar", methods=["POST"])
def adicionar_checklist(dia_id):
    texto = request.form.get("texto", "").strip()
    if texto:
        checklist_service.adicionar_item(dia_id, texto)
    return redirect(url_for("planejamento.ver_dia", dia_id=dia_id))


@bp.route("/checklist/<int:item_id>/remover", methods=["POST"])
def remover_checklist(item_id):
    from app.models import ChecklistItem
    item = ChecklistItem.query.get_or_404(item_id)
    dia_id = item.dia_id
    checklist_service.remover_item(item_id)
    return redirect(url_for("planejamento.ver_dia", dia_id=dia_id))

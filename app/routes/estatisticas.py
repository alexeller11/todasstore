from flask import Blueprint, render_template, redirect, url_for, flash

from app.models import Semana, InsightSemanal, Loja
from app.extensions import db, limiter
from app.services import analytics_service
from app.ai import ai_service, prompts

bp = Blueprint("estatisticas", __name__, url_prefix="/estatisticas")


@bp.route("/semana/<int:semana_id>")
def ver(semana_id):
    semana = Semana.query.get_or_404(semana_id)
    stats = analytics_service.progresso_semana(semana_id)
    insight = (
        InsightSemanal.query.filter_by(semana_id=semana_id)
        .order_by(InsightSemanal.criado_em.desc())
        .first()
    )
    return render_template("estatisticas.html", semana=semana, stats=stats, insight=insight)


@bp.route("/semana/<int:semana_id>/gerar-insight", methods=["POST"])
@limiter.limit("5 per minute")
def gerar_insight(semana_id):
    semana = Semana.query.get_or_404(semana_id)
    loja = Loja.query.first()
    resumo = analytics_service.resumo_textual_semana(semana_id)

    try:
        system_prompt, user_prompt = prompts.prompt_insight_semanal(loja, resumo)
        texto = ai_service.gerar_texto(system_prompt, user_prompt)

        insight = InsightSemanal(semana_id=semana_id, texto=texto)
        db.session.add(insight)
        db.session.commit()
        flash("Novo insight gerado!", "success")
    except Exception as e:
        flash(f"Não consegui gerar agora: {e}", "danger")

    return redirect(url_for("estatisticas.ver", semana_id=semana_id))

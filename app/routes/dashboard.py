from datetime import date
from flask import Blueprint, render_template, redirect, url_for

from app.models import Loja, Dia
from app.services.planner_service import obter_ou_criar_mes
from app.services import analytics_service

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def inicio():
    loja = Loja.query.first()
    if not loja or not loja.onboarding_concluido:
        return redirect(url_for("onboarding.bem_vinda"))

    hoje = date.today()
    mes = obter_ou_criar_mes(hoje.year, hoje.month)

    dia_hoje = Dia.query.filter_by(data=hoje).first()

    # próximo conteúdo: primeiro dia a partir de hoje que ainda não está completo
    proximo_conteudo = (
        Dia.query.filter(Dia.data >= hoje)
        .order_by(Dia.data.asc())
        .filter(
            (Dia.ideia_story.isnot(None)) | (Dia.tem_post.is_(True))
        )
        .first()
    )

    stats = analytics_service.progresso_mes(mes.id)

    return render_template(
        "dashboard.html",
        loja=loja,
        mes=mes,
        dia_hoje=dia_hoje,
        proximo_conteudo=proximo_conteudo,
        stats=stats,
        hoje=hoje,
    )

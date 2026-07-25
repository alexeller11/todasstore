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

    # semana atual, para a faixa de calendário rápido na home
    semana_atual = dia_hoje.semana if dia_hoje else None

    # se a semana atual ainda não tem NENHUM conteúdo gerado, sugerimos
    # ativamente gerar o planejamento (em vez de deixar a lojista descobrir
    # sozinha que precisa ir lá dentro da semana pra clicar em gerar)
    semana_sem_conteudo = bool(
        semana_atual and not any(d.ideia_story or d.tem_post for d in semana_atual.dias)
    )

    return render_template(
        "dashboard.html",
        loja=loja,
        mes=mes,
        dia_hoje=dia_hoje,
        semana_atual=semana_atual,
        semana_sem_conteudo=semana_sem_conteudo,
        proximo_conteudo=proximo_conteudo,
        stats=stats,
        hoje=hoje,
    )

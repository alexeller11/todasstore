import json
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.extensions import db
from app.models import Concorrente, AnaliseConcorrente, Loja
from app.services import instagram_service
from app.ai import ai_service, prompts

bp = Blueprint("concorrentes", __name__, url_prefix="/concorrentes")


@bp.route("/")
def listar():
    concorrentes = Concorrente.query.order_by(Concorrente.criado_em.desc()).all()
    return render_template("concorrentes.html", concorrentes=concorrentes)


@bp.route("/adicionar", methods=["POST"])
def adicionar():
    usuario = request.form.get("instagram", "").strip().lstrip("@")
    if usuario:
        concorrente = Concorrente(instagram=usuario, apelido=request.form.get("apelido", ""))
        db.session.add(concorrente)
        db.session.commit()
        flash(f"@{usuario} adicionado(a) para acompanhamento.", "success")
    return redirect(url_for("concorrentes.listar"))


@bp.route("/<int:concorrente_id>/remover", methods=["POST"])
def remover(concorrente_id):
    c = Concorrente.query.get_or_404(concorrente_id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("concorrentes.listar"))


@bp.route("/<int:concorrente_id>")
def ver(concorrente_id):
    concorrente = Concorrente.query.get_or_404(concorrente_id)
    ultima_analise = (
        AnaliseConcorrente.query.filter_by(concorrente_id=concorrente_id)
        .order_by(AnaliseConcorrente.criado_em.desc())
        .first()
    )
    return render_template("concorrente_detalhe.html", concorrente=concorrente, ultima_analise=ultima_analise)


@bp.route("/<int:concorrente_id>/observacoes", methods=["POST"])
def salvar_observacoes(concorrente_id):
    concorrente = Concorrente.query.get_or_404(concorrente_id)
    concorrente.observacoes_stories = request.form.get("observacoes_stories", "")
    db.session.commit()
    flash("Observações sobre os Stories salvas.", "success")
    return redirect(url_for("concorrentes.ver", concorrente_id=concorrente_id))


@bp.route("/<int:concorrente_id>/analisar", methods=["POST"])
def analisar(concorrente_id):
    concorrente = Concorrente.query.get_or_404(concorrente_id)
    loja = Loja.query.first()

    dados_publicos = instagram_service.coletar_dados_publicos(concorrente.instagram)
    texto_dados = instagram_service.montar_texto_dados_para_ia(
        dados_publicos, concorrente.observacoes_stories
    )

    try:
        system_prompt, user_prompt = prompts.prompt_analise_concorrente(
            loja, concorrente, texto_dados, concorrente.observacoes_stories
        )
        resumo = ai_service.gerar_texto(system_prompt, user_prompt)

        analise = AnaliseConcorrente(
            concorrente_id=concorrente.id,
            dados_brutos=json.dumps(dados_publicos, ensure_ascii=False),
            resumo_ia=resumo,
        )
        db.session.add(analise)
        db.session.commit()
        flash("Análise concluída! 🔎", "success")
    except Exception as e:
        flash(f"Não consegui analisar agora: {e}", "danger")

    return redirect(url_for("concorrentes.ver", concorrente_id=concorrente_id))

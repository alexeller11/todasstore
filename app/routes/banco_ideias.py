from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Ideia

bp = Blueprint("banco_ideias", __name__, url_prefix="/ideias")


@bp.route("/")
def listar():
    busca = request.args.get("busca", "").strip()
    apenas_favoritas = request.args.get("favoritas") == "1"
    tipo = request.args.get("tipo", "").strip()

    query = Ideia.query
    if busca:
        like = f"%{busca}%"
        query = query.filter(
            db.or_(Ideia.titulo.ilike(like), Ideia.conteudo.ilike(like), Ideia.tags.ilike(like))
        )
    if apenas_favoritas:
        query = query.filter_by(favorito=True)
    if tipo in ("story", "reels", "feed"):
        query = query.filter_by(tipo=tipo)

    ideias = query.order_by(Ideia.criado_em.desc()).all()
    return render_template(
        "banco_ideias.html", ideias=ideias, busca=busca, apenas_favoritas=apenas_favoritas, tipo=tipo
    )


@bp.route("/nova", methods=["POST"])
def nova():
    ideia = Ideia(
        titulo=request.form.get("titulo", "Ideia sem título"),
        tipo=request.form.get("tipo", "story"),
        conteudo=request.form.get("conteudo", ""),
        legenda=request.form.get("legenda", ""),
        cta=request.form.get("cta", ""),
        tags=request.form.get("tags", ""),
        origem="manual",
    )
    db.session.add(ideia)
    db.session.commit()
    flash("Ideia salva no seu banco de ideias! 💡", "success")
    return redirect(url_for("banco_ideias.listar"))


@bp.route("/<int:ideia_id>/favoritar", methods=["POST"])
def favoritar(ideia_id):
    ideia = Ideia.query.get_or_404(ideia_id)
    ideia.favorito = not ideia.favorito
    db.session.commit()
    return redirect(url_for("banco_ideias.listar"))


@bp.route("/<int:ideia_id>/excluir", methods=["POST"])
def excluir(ideia_id):
    ideia = Ideia.query.get_or_404(ideia_id)
    db.session.delete(ideia)
    db.session.commit()
    flash("Ideia removida.", "info")
    return redirect(url_for("banco_ideias.listar"))


@bp.route("/salvar-do-dia/<int:dia_id>/<tipo>", methods=["POST"])
def salvar_do_dia(dia_id, tipo):
    """Copia o conteúdo de um dia (story/reels/feed) para o Banco de Ideias,
    marcando origem='ia'. Resolve a sensação 'gero e some', dando à lojista
    um botão de 1 clique para preservar um conteúdo que gostou."""
    from app.models import Dia
    dia = Dia.query.get_or_404(dia_id)

    if tipo == "story":
        conteudo = dia.ideia_story
    elif tipo == "reels":
        conteudo = dia.ideia_reels
    elif tipo == "feed":
        conteudo = dia.ideia_feed
    else:
        flash("Tipo de conteúdo inválido.", "danger")
        return redirect(url_for("planejamento.ver_dia", dia_id=dia_id))

    if not conteudo:
        flash("Nada para salvar: ainda não há ideia desse tipo neste dia. "
              "Gere uma ideia antes de salvar no Banco de Ideias.", "warning")
        return redirect(url_for("planejamento.ver_dia", dia_id=dia_id))

    nome_tipo = {"story": "Story", "reels": "Reels", "feed": "Feed"}[tipo]
    data_fmt = dia.data.strftime("%d/%m/%Y")
    titulo = f"{nome_tipo} de {dia.dia_semana.capitalize()} ({data_fmt})"

    ideia = Ideia(
        titulo=titulo,
        tipo=tipo,
        conteudo=conteudo,
        legenda=dia.legenda or "",
        cta=dia.cta or "",
        tags=dia.objetivo or "",
        origem="ia",
    )
    db.session.add(ideia)
    db.session.commit()
    flash(f"{nome_tipo} salvo no Banco de Ideias! 💾", "success")
    return redirect(url_for("planejamento.ver_dia", dia_id=dia_id))


@bp.route("/usar-no-dia/<int:ideia_id>/<int:dia_id>", methods=["POST"])
def usar_no_dia(ideia_id, dia_id):
    """Copia uma ideia salva para dentro de um dia do planejamento."""
    from app.models import Dia
    ideia = Ideia.query.get_or_404(ideia_id)
    dia = Dia.query.get_or_404(dia_id)

    if ideia.tipo == "story":
        dia.ideia_story = ideia.conteudo
    elif ideia.tipo == "reels":
        dia.ideia_reels = ideia.conteudo
        dia.tem_post = True
    elif ideia.tipo == "feed":
        dia.ideia_feed = ideia.conteudo
        dia.tem_post = True

    dia.legenda = ideia.legenda or dia.legenda
    dia.cta = ideia.cta or dia.cta

    db.session.commit()
    flash("Ideia aplicada ao dia! ✅", "success")
    return redirect(url_for("planejamento.ver_dia", dia_id=dia_id))

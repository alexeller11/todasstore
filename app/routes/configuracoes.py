from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Loja

bp = Blueprint("configuracoes", __name__, url_prefix="/configuracoes")


@bp.route("/", methods=["GET", "POST"])
def ver():
    loja = Loja.query.first()
    if not loja:
        loja = Loja(nome="Minha Loja")
        db.session.add(loja)
        db.session.commit()

    if request.method == "POST":
        loja.nome = request.form.get("nome", loja.nome)
        loja.logo_url = request.form.get("logo_url", loja.logo_url)
        loja.instagram = request.form.get("instagram", loja.instagram)
        loja.whatsapp = request.form.get("whatsapp", loja.whatsapp)
        loja.cidade = request.form.get("cidade", loja.cidade)
        loja.segmento = request.form.get("segmento", loja.segmento)
        loja.horario_funcionamento = request.form.get("horario_funcionamento", loja.horario_funcionamento)
        loja.estilo = request.form.get("estilo", loja.estilo)
        loja.publico = request.form.get("publico", loja.publico)
        loja.faixa_preco = request.form.get("faixa_preco", loja.faixa_preco)
        loja.produtos = request.form.get("produtos", loja.produtos)
        loja.tom_de_voz = request.form.get("tom_de_voz", loja.tom_de_voz)
        loja.objetivos = request.form.get("objetivos", loja.objetivos)

        db.session.commit()
        flash("Configurações salvas com sucesso!", "success")
        return redirect(url_for("configuracoes.ver"))

    return render_template("configuracoes.html", loja=loja)

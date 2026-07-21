from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Loja

bp = Blueprint("onboarding", __name__)


@bp.route("/bem-vinda", methods=["GET", "POST"])
def bem_vinda():
    loja = Loja.query.first()

    if request.method == "POST":
        if not loja:
            loja = Loja()
            db.session.add(loja)

        loja.nome = request.form.get("nome", "").strip()
        loja.cidade = request.form.get("cidade", "").strip()
        loja.instagram = request.form.get("instagram", "").strip()
        loja.estilo = request.form.get("estilo", "").strip()
        loja.publico = request.form.get("publico", "").strip()
        loja.faixa_preco = request.form.get("faixa_preco", "").strip()
        loja.produtos = request.form.get("produtos", "").strip()
        loja.tom_de_voz = request.form.get("tom_de_voz", "").strip()
        loja.objetivos = request.form.get("objetivos", "").strip()
        # Diferenciais e dores do público sao OPCIONAIS mas fazem a IA gerar
        # conteúdo muito menos genérico - por isso entram já no onboarding.
        loja.diferenciais = request.form.get("diferenciais", "").strip()
        loja.dores_do_publico = request.form.get("dores_do_publico", "").strip()
        loja.onboarding_concluido = True

        db.session.commit()
        flash("Prontinho! Seu perfil foi salvo. 💖", "success")
        return redirect(url_for("dashboard.inicio"))

    return render_template("onboarding.html", loja=loja)

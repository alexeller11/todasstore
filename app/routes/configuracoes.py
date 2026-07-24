from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Loja

bp = Blueprint("configuracoes", __name__, url_prefix="/configuracoes")


import os
from werkzeug.utils import secure_filename

EXTENSOES_LOGO_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}
TAMANHO_MAXIMO_LOGO_MB = 3


def _extensao_valida(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSOES_LOGO_PERMITIDAS


@bp.route("/", methods=["GET", "POST"])
def ver():
    loja = Loja.query.first()
    if not loja:
        loja = Loja(nome="Minha Loja")
        db.session.add(loja)
        db.session.commit()

    if request.method == "POST":
        if 'logo_file' in request.files:
            file = request.files['logo_file']
            if file.filename != '':
                if not _extensao_valida(file.filename):
                    flash("Formato de imagem não suportado. Use PNG, JPG ou WEBP.", "danger")
                    return redirect(url_for("configuracoes.ver"))

                file.seek(0, os.SEEK_END)
                tamanho_mb = file.tell() / (1024 * 1024)
                file.seek(0)
                if tamanho_mb > TAMANHO_MAXIMO_LOGO_MB:
                    flash(f"A imagem passa do limite de {TAMANHO_MAXIMO_LOGO_MB}MB. Tente uma menor.", "danger")
                    return redirect(url_for("configuracoes.ver"))

                filename = secure_filename(file.filename)
                upload_folder = os.path.join("app", "static", "uploads")
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                loja.logo_url = url_for("static", filename=f"uploads/{filename}")
            else:
                loja.logo_url = request.form.get("logo_url", loja.logo_url)
        else:
            loja.logo_url = request.form.get("logo_url", loja.logo_url)
            
        loja.nome = request.form.get("nome", loja.nome)
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
        loja.diferenciais = request.form.get("diferenciais", loja.diferenciais)
        loja.dores_do_publico = request.form.get("dores_do_publico", loja.dores_do_publico)

        db.session.commit()
        flash("Configurações salvas com sucesso!", "success")
        return redirect(url_for("configuracoes.ver"))

    return render_template("configuracoes.html", loja=loja)

import os
from flask import Flask

from config import Config
from app.extensions import db, migrate


def _garantir_colunas_novas():
    """Como o projeto não usa migrations formais (Alembic), db.create_all() só cria
    tabelas que não existem - não adiciona colunas novas em tabelas já existentes.
    Esta função cobre esse caso de forma simples e segura para adicionar colunas novas
    sem apagar dados existentes."""
    from sqlalchemy import text, inspect

    inspetor = inspect(db.engine)
    if "semana" not in inspetor.get_table_names():
        return

    colunas_existentes = {c["name"] for c in inspetor.get_columns("semana")}
    if "promocao" not in colunas_existentes:
        try:
            db.session.execute(text("ALTER TABLE semana ADD COLUMN promocao TEXT"))
            db.session.commit()
        except Exception:
            db.session.rollback()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # garante que a pasta instance/ exista (para o SQLite local)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    from app.extensions import csrf
    csrf.init_app(app)

    from app.models import models  # noqa: garante que os modelos sejam registrados

    from app.routes import dashboard, onboarding, planejamento, banco_ideias
    from app.routes import concorrentes, configuracoes, estatisticas

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(onboarding.bp)
    app.register_blueprint(planejamento.bp)
    app.register_blueprint(banco_ideias.bp)
    app.register_blueprint(concorrentes.bp)
    app.register_blueprint(configuracoes.bp)
    app.register_blueprint(estatisticas.bp)

    @app.route("/sw.js")
    def service_worker():
        from flask import send_from_directory
        return send_from_directory(
            os.path.join(app.root_path, "static"), "sw.js", mimetype="application/javascript"
        )

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template
        return render_template('500.html'), 500

    @app.context_processor
    def injetar_globais():
        from app.models import Loja
        loja_atual = Loja.query.first()
        return {"loja_atual": loja_atual}

    with app.app_context():
        db.create_all()
        _garantir_colunas_novas()

    return app

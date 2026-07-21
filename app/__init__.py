import os
from flask import Flask

from config import Config
from app.extensions import db, migrate


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
        # Em produção (DATABASE_URL = PostgreSQL do Render), o esquema é
        # controlado por Alembic via `scripts/run_migrations.py` (render.yaml
        # preDeployCommand). db.create_all() NÃO deve rodar em produção porque:
        #   1) ele tenta criar TODAS as tabelas atuais (incl. as novas) e em
        #      PostgreSQL isso pode abortar a transaction (InFailedSqlTransaction)
        #      e quebrar as migrations subsequentes;
        #   2) ele mascara migrations não-aplicadas, dando a ilusão de
        #      "esquema em dia" enquanto o alembic_version está atrasado.
        # Em dev (SQLite local) ele é uma rede de segurança: cria tudo a
        # partir dos modelos atuais, ignorando migrations.
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        is_producao = uri.startswith("postgresql")
        skip_create_all = is_producao or os.environ.get("TODASSTORE_SKIP_CREATE_ALL") == "1"
        if skip_create_all:
            app.logger.info(
                "[create_app] esquema controlado por migrations Alembic; "
                "db.create_all() NAO sera rodado."
            )
        else:
            try:
                db.create_all()
            except Exception as e:
                app.logger.warning(
                    f"db.create_all() falhou (provavelmente por migration "
                    f"pendente): {e}"
                )
                try:
                    db.session.rollback()
                except Exception:
                    pass
                db.engine.dispose()

    return app

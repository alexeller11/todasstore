import os
from flask import Flask

from config import Config
from app.extensions import db, migrate, limiter


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # garante que a pasta instance/ exista (para o SQLite local)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    from app.extensions import csrf
    csrf.init_app(app)
    limiter.init_app(app)

    from app.models import models  # noqa: garante que os modelos sejam registrados

    from app.routes import dashboard, onboarding, planejamento, banco_ideias
    from app.routes import concorrentes, configuracoes, estatisticas
    from app.routes import admin

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(onboarding.bp)
    app.register_blueprint(planejamento.bp)
    app.register_blueprint(banco_ideias.bp)
    app.register_blueprint(concorrentes.bp)
    app.register_blueprint(configuracoes.bp)
    app.register_blueprint(estatisticas.bp)
    app.register_blueprint(admin.bp)

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

    @app.errorhandler(429)
    def limite_de_pedidos_excedido(e):
        from flask import request, redirect, flash
        flash("Muitos pedidos de geração por IA em pouco tempo. Espere um minutinho e tente de novo. 🙏", "danger")
        destino = request.referrer or "/"
        return redirect(destino)

    @app.context_processor
    def injetar_globais():
        from datetime import date
        from app.models import Loja
        loja_atual = Loja.query.first()
        return {"loja_atual": loja_atual, "hoje": date.today()}

        with app.app_context():
            uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            is_producao = uri.startswith("postgresql")
            if not is_producao:
                # Development (SQLite) – cria as tabelas se ainda não existirem
                try:
                    db.create_all()
                except Exception as e:
                    app.logger.warning(f"db.create_all() falhou: {e}")
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    db.engine.dispose()
            else:
                app.logger.info("[create_app] Production environment – schema managed by migrations")

    return app


# NOTE: Auto‑sync schema logic removed – schema now managed exclusively by Alembic migrations.
# The previous `_auto_sync_schema_em_producao` helper has been deprecated.
# If manual schema adjustments are ever required, use Alembic migration scripts.


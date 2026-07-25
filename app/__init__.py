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
        # Em producao (DATABASE_URL = PostgreSQL do Render), o esquema e
        # controlado por migrations/sincronizacao manual. db.create_all() NÃO
        # adiciona colunas novas em tabelas existentes em PostgreSQL, e tentar
        # faze-lo numa transacao DDL pode abortar a transacao inteira
        # (causa raiz do bug InFailedSqlTransaction).
        # Por isso, em PostgreSQL:
        #   - pulamos db.create_all();
        #   - rodamos AUTO-SYNC defensivo: cria colunas/tabelas faltantes via
        #     SQL "IF NOT EXISTS". Isto desbloqueia o site quando migrations
        #     nao rodaram (ex.: Blueprint do Render nao disparou o preDeploy).
        # Em dev (SQLite local), db.create_all() e a rede de seguranca.
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        is_producao = uri.startswith("postgresql")
        skip_create_all = is_producao or os.environ.get("TODASSTORE_SKIP_CREATE_ALL") == "1"
        if skip_create_all:
            app.logger.info(
                "[create_app] PostgreSQL detectado - esquema controlado por "
                "migrations/sync manual; db.create_all() NAO sera rodado."
            )
            try:
                _auto_sync_schema_em_producao(app)
            except Exception as e:
                app.logger.warning(f"[create_app] auto-sync falhou: {e}")
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


def _auto_sync_schema_em_producao(app):
    """Verifica colunas/tabelas essenciais e cria via SQL idempotente.

    Equivalente a migration 0002. Idempotente - seguro rodar a cada boot.
    Em qualquer erro, faz rollback e loga; nao bloqueia o startup.

    Compativel com PostgreSQL (producao) E SQLite (dev/test): usamos o
    SQLAlchemy Inspector para detectar o estado antes de emitir DDL.
    """
    from sqlalchemy import text, inspect

    inspector = inspect(db.engine)
    is_sqlite = db.engine.dialect.name == "sqlite"
    pk_declaration = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"

    # 1) dia.descricao_visual (SQLite nao suporta ADD COLUMN IF NOT EXISTS)
    if "dia" in inspector.get_table_names():
        colunas_dia = {c["name"] for c in inspector.get_columns("dia")}
        if "descricao_visual" not in colunas_dia:
            app.logger.info("[auto-sync] adicionando coluna dia.descricao_visual")
            try:
                db.session.execute(text(
                    "ALTER TABLE dia ADD COLUMN descricao_visual TEXT"
                ))
                db.session.commit()
            except Exception as e:
                app.logger.warning(f"[auto-sync] falha add coluna descricao_visual: {e}")
                db.session.rollback()

    # 2) versao_conteudo (CREATE TABLE IF NOT EXISTS - suportado por ambos)
    if "versao_conteudo" not in inspector.get_table_names():
        app.logger.info("[auto-sync] criando tabela versao_conteudo")
        sql_create = (
            "CREATE TABLE IF NOT EXISTS versao_conteudo ("
            f"  id {pk_declaration},"
            "  dia_id INTEGER NOT NULL REFERENCES dia(id),"
            "  tipo VARCHAR(15) NOT NULL,"
            "  conteudo TEXT,"
            "  descricao_visual TEXT,"
            "  legenda TEXT,"
            "  cta VARCHAR(255),"
            "  formato VARCHAR(80),"
            "  objetivo VARCHAR(120),"
            "  tempo_estimado VARCHAR(60),"
            "  criado_em TIMESTAMP"
            ")"
        )
        try:
            db.session.execute(text(sql_create))
            db.session.commit()
        except Exception as e:
            app.logger.warning(f"[auto-sync] falha create tabela versao_conteudo: {e}")
            db.session.rollback()

    # libera a sessao e dispone o engine: garante que proximas requests
    # peguem conexoes frescas (nao eventual conexao com transacao abortada)
    db.session.remove()
    db.engine.dispose()
    app.logger.info("[auto-sync] schema sincronizado. engine disposed.")

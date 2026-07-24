"""Rotas administrativas de emergencia.

Estas rotas existem para situacoes de emergencia em producao onde as migrations
nao rodaram (ex.: Blueprint do Render nao disparou preDeployCommand) e o
esquema do banco esta desalinhado com os modelos SQLAlchemy - fazendo o site
inteiro quebrar com `UndefinedColumn` + `InFailedSqlTransaction`.

A rota `/admin/sync-schema` força a criacao de colunas/tabelas faltantes usando
SQL `IF NOT EXISTS` (compativel com PostgreSQL e SQLite via Inspector),
sem depender de Alembic. Idempotente e segura para rodar multiplas vezes.

Protecao: requer um token passado via query string `?token=...` cujo valor deve
ser igual ao da variavel de ambiente `ADMIN_SYNC_TOKEN`. Em dev/test local (sem
essa variavel definida) a rota funciona sem auth, para facilitar o trabalho no
dia a dia. Em producao (FLASK_ENV=production), a rota SEMPRE exige o token -
se `ADMIN_SYNC_TOKEN` nao estiver configurada no Render, a rota fica bloqueada
por padrao (falha fechada), em vez de ficar aberta para qualquer pessoa.
"""
import os

from flask import Blueprint, current_app, request, jsonify
from sqlalchemy import text, inspect

from app.extensions import db

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _autenticado():
    """Em dev/test (sem ADMIN_SYNC_TOKEN definida), permite. Em producao,
    exige `?token=` igual a env `ADMIN_SYNC_TOKEN` - e bloqueia por padrao
    (falha fechada) se essa variavel nao tiver sido configurada."""
    esperado = os.environ.get("ADMIN_SYNC_TOKEN")
    em_producao = os.environ.get("FLASK_ENV", "production") == "production"

    if not esperado:
        # Sem token configurado: so permite fora de producao (dev/test).
        # Em producao sem token configurado, bloqueia por seguranca.
        return not em_producao

    recebido = request.args.get("token", "")
    if len(recebido) != len(esperado):
        return False
    return all(a == b for a, b in zip(recebido, esperado))


def _coluna_existe(inspector, tabela, coluna):
    if tabela not in inspector.get_table_names():
        return False
    return coluna in {c["name"] for c in inspector.get_columns(tabela)}


def _pk_declaration(is_sqlite):
    return "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"


@bp.route("/sync-schema", methods=["GET", "POST"])
def sync_schema():
    """Sincroniza o esquema do banco faltando colunas/tabelas essenciais.

    Equivalente idempotente da migration 0002_add_descricao_visual_e_versao_conteudo.
    Compativel com PostgreSQL (producao) e SQLite (dev/test)."""
    if not _autenticado():
        return jsonify({"ok": False, "erro": "token ausente ou invalido"}), 403

    relatorio = []
    try:
        inspector = inspect(db.engine)
        is_sqlite = db.engine.dialect.name == "sqlite"

        # 1) dia.descricao_visual
        if not _coluna_existe(inspector, "dia", "descricao_visual"):
            if "dia" in inspector.get_table_names():
                try:
                    # SQLite nao aceita "IF NOT EXISTS"; inspecionamos antes
                    db.session.execute(text(
                        "ALTER TABLE dia ADD COLUMN descricao_visual TEXT"
                    ))
                    db.session.commit()
                    relatorio.append(("dia.descricao_visual", "adicionado"))
                except Exception as e:
                    db.session.rollback()
                    relatorio.append(("dia.descricao_visual", f"ERRO: {e}"))
            else:
                relatorio.append(("dia.descricao_visual", "tabela dia nao existe"))
        else:
            relatorio.append(("dia.descricao_visual", "ja existe"))

        # 2) versao_conteudo
        if "versao_conteudo" not in inspector.get_table_names():
            try:
                pk = _pk_declaration(is_sqlite)
                sql = (
                    "CREATE TABLE IF NOT EXISTS versao_conteudo ("
                    f"  id {pk},"
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
                db.session.execute(text(sql))
                db.session.commit()
                relatorio.append(("versao_conteudo", "criada"))
            except Exception as e:
                db.session.rollback()
                relatorio.append(("versao_conteudo", f"ERRO: {e}"))
        else:
            relatorio.append(("versao_conteudo", "ja existe"))

        # 3) Atualiza alembic_version (se a tabela existir) para a 0002
        try:
            if "alembic_version" in inspect(db.engine).get_table_names():
                db.session.execute(
                    text("UPDATE alembic_version SET version_num = '0002_descricao_versoes'")
                )
                db.session.commit()
                relatorio.append(("alembic_version", "set para 0002_descricao_versoes"))
            else:
                relatorio.append(("alembic_version", "nao existe - opcional"))
        except Exception as e:
            db.session.rollback()
            relatorio.append(("alembic_version", f"opcional - pulado ({e})"))

        # 4) dispose do engine para limpar conexoes com transacao abortada
        #    (CRITICO: isto quebra o ciclo InFailedSqlTransaction em producao)
        db.session.remove()
        db.engine.dispose()
        relatorio.append(("engine", "disposed - pool de conexoes reiniciado"))

        return jsonify({
            "ok": True,
            "relatorio": [{"item": r[0], "status": r[1]} for r in relatorio],
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "erro": str(e)}), 500

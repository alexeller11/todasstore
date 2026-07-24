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

from flask import Blueprint, current_app, request, jsonify, render_template_string
from sqlalchemy import text, inspect

from app.extensions import db, csrf

bp = Blueprint("admin", __name__, url_prefix="/admin")
csrf.exempt(bp)


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


_TABELAS_EM_ORDEM_DE_EXCLUSAO = [
    "checklist_item",
    "versao_conteudo",
    "insight_semanal",
    "dia",
    "semana",
    "mes",
    "analise_concorrente",
    "concorrente",
    "ideia",
    "loja",
]

_PAGINA_CONFIRMACAO = """
<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>Resetar dados - Todas Store</title>
<style>
  body { font-family: sans-serif; background:#FFF6F0; display:flex; align-items:center;
         justify-content:center; height:100vh; margin:0; }
  .caixa { background:white; padding:32px; border-radius:16px; max-width:420px;
           box-shadow:0 4px 16px rgba(0,0,0,.08); text-align:center; }
  h2 { color:#6B2C4C; }
  ul { text-align:left; color:#555; }
  button { background:#B23A48; color:white; border:none; padding:12px 24px;
           border-radius:24px; font-weight:bold; cursor:pointer; font-size:1rem; }
  button:hover { opacity:.9; }
</style></head>
<body>
  <div class="caixa">
    <h2>⚠️ Resetar TODOS os dados?</h2>
    <p>Isso vai apagar permanentemente, para sempre:</p>
    <ul>
      <li>Perfil da loja (a lojista fará o onboarding do zero)</li>
      <li>Todo o planejamento (meses, semanas, dias, checklist)</li>
      <li>Banco de ideias</li>
      <li>Concorrentes e análises</li>
    </ul>
    <p><strong>Não tem como desfazer.</strong> Use antes de entregar o app para um cliente novo.</p>
    <form method="POST">
      <input type="hidden" name="token" value="{{ token }}">
      <input type="hidden" name="confirmar" value="RESETAR">
      <button type="submit">Sim, apagar tudo e começar do zero</button>
    </form>
  </div>
</body></html>
"""


@bp.route("/reset-dados", methods=["GET", "POST"])
def reset_dados():
    """Apaga todos os dados (loja, planejamento, banco de ideias, concorrentes),
    preservando o esquema do banco intacto - para entregar o app "zerado" a um
    novo cliente. GET mostra uma tela de confirmacao; a exclusao real só
    acontece no POST com `confirmar=RESETAR`, para nao rodar sozinha se o link
    (com o token) for aberto sem querer por alguem ou por um preview de link."""
    if not _autenticado():
        return jsonify({"ok": False, "erro": "token ausente ou invalido"}), 403

    if request.method == "GET":
        token = request.args.get("token", "")
        return render_template_string(_PAGINA_CONFIRMACAO, token=token)

    if request.form.get("confirmar") != "RESETAR":
        return jsonify({"ok": False, "erro": "confirmacao ausente"}), 400

    relatorio = []
    try:
        inspector = inspect(db.engine)
        tabelas_existentes = set(inspector.get_table_names())

        for tabela in _TABELAS_EM_ORDEM_DE_EXCLUSAO:
            if tabela not in tabelas_existentes:
                relatorio.append((tabela, "tabela nao existe - pulado"))
                continue
            try:
                resultado = db.session.execute(text(f"DELETE FROM {tabela}"))
                db.session.commit()
                relatorio.append((tabela, f"{resultado.rowcount} registro(s) apagado(s)"))
            except Exception as e:
                db.session.rollback()
                relatorio.append((tabela, f"ERRO: {e}"))

        db.session.remove()
        db.engine.dispose()
        relatorio.append(("engine", "disposed - pool de conexoes reiniciado"))

        return jsonify({
            "ok": True,
            "mensagem": "Dados resetados. Acesse o app normalmente - ele vai pedir o onboarding do zero.",
            "relatorio": [{"item": r[0], "status": r[1]} for r in relatorio],
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "erro": str(e)}), 500

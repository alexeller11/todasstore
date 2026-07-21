"""Aplica migrations Alembic de forma idempotente para deploy no Render.

Este script e separado do create_app() porque rodar stamp/upgrade e o runtime
no MESMO contexto compartilha socket de conexao do SQLAlchemy. Se qualquer
DDL falha (ex.: coluna ja existe numa migration nao-idempotente), a transaction
PostgreSQL fica "aborted" e TODA query seguinte na mesma conexao recebe
`psycopg2.errors.InFailedSqlTransaction` ate um ROLLBACK explicito.

Solucao: rodar o preDeploy num PROCESS separado que faz o trabalho, da
dispose no engine ao final (fecha todas as conexoes) e encerra. O gunicorn
que sobe em seguida comeca com um pool novo e limpo.

Fluxo:
1. Tenta stamp na baseline 0001 SE o banco ja tem tabelas mas nao tem
   alembic_version (banco legado de producao pre-migrations).
2. Roda upgrade (idempotente: a 0002 tem guarda `if not exists`).

Uso:
    python scripts/run_migrations.py
"""
import sys
from pathlib import Path

# Garante que o diretorio raiz do projeto esteja no path (quando executado
# como `python scripts/run_migrations.py` a partir da raiz)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Sinaliza ao create_app() para NAO rodar db.create_all(). Mesmo em dev SQLite,
# isto garante que o script de migracoes veja o esquema REAL existente e
# aplique apenas o delta via Alembic. Em producao (PostgreSQL) isto e critico
# para evitar o bug InFailedSqlTransaction (db.create_all() criando tabelas
# novas dentro de transacao DDL e aborta-la).
import os
os.environ["TODASSTORE_SKIP_CREATE_ALL"] = "1"

from app import create_app                    # noqa: E402
from app.extensions import db                  # noqa: E402
import sqlalchemy                              # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        # Importa APOS criar contexto para nao acoplar em estado global.
        from flask_migrate import stamp, upgrade

        inspector = sqlalchemy.inspect(db.engine)
        tabelas = set(inspector.get_table_names())

        tem_tabelas = len(tabelas - {"alembic_version"}) > 0
        tem_alembic_version = "alembic_version" in tabelas

        if tem_tabelas and not tem_alembic_version:
            print("[migrations] banco legado sem alembic_version -> "
                  "stamp na baseline 0001_baseline_producao")
            stamp(directory=str(ROOT / "migrations"),
                  revision="0001_baseline_producao")
        else:
            print(f"[migrations] estado: {len(tabelas)} tabelas, "
                  f"alembic_version={'sim' if tem_alembic_version else 'nao'}")

        print("[migrations] rodando upgrade...")
        upgrade(directory=str(ROOT / "migrations"))
        print("[migrations] upgrade OK")

    # CRUCIAL: libera TODAS as conexoes abertas pelo processo de migration.
    # Sem isso, conexoes com transaction abortada poderiam persistir.
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    print("[migrations] engine disposed; processo de migracao concluido.")


if __name__ == "__main__":
    main()

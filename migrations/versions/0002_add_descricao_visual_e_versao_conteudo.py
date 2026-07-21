"""adicional: dia.descricao_visual e nova tabela versao_conteudo

Revision ID: 0002_descricao_versoes
Revises: 0001_baseline_producao
Create Date: 2026-07-21 14:23:12.277330

Esta revision eh INCREMENTAL sobre a baseline 0001. Ela:
- adiciona a coluna dia.descricao_visual (cena concreta da foto/video)
- adiciona a tabela versao_conteudo (historico de versoes antes de regenerar)

IMPORTANTE (producao - Render/PostgreSQL - banco JA existe com dados):
    flask db stamp 0001_baseline_producao   # marca o esquema antigo como ja aplicado
    flask db upgrade                         # ro somente esta revision (add col + tabela)

DEV novo (SQLite vazio):
    flask db upgrade   # aplica a baseline 0001 (cria tudo) e em seguida esta 0002

Em ambos os casos NENHUM dado existente e alterado ou removido - sao puros "add".
"""
from alembic import op
import sqlalchemy as sa


revision = '0002_descricao_versoes'
down_revision = '0001_baseline_producao'
branch_labels = None
depends_on = None


def _coluna_existe(bind, tabela, coluna):
    from sqlalchemy import inspect
    insp = inspect(bind)
    if tabela not in insp.get_table_names():
        return False
    return coluna in {c["name"] for c in insp.get_columns(tabela)}


def upgrade():
    bind = op.get_bind()

    # 1) dia.descricao_visual
    if not _coluna_existe(bind, "dia", "descricao_visual"):
        op.add_column(
            "dia",
            sa.Column("descricao_visual", sa.Text(), nullable=True),
        )

    # 2) tabela versao_conteudo (so cria se nao existir - guarda idempotente)
    if "versao_conteudo" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "versao_conteudo",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dia_id", sa.Integer(), nullable=False),
            sa.Column("tipo", sa.String(length=15), nullable=False),
            sa.Column("conteudo", sa.Text(), nullable=True),
            sa.Column("descricao_visual", sa.Text(), nullable=True),
            sa.Column("legenda", sa.Text(), nullable=True),
            sa.Column("cta", sa.String(length=255), nullable=True),
            sa.Column("formato", sa.String(length=80), nullable=True),
            sa.Column("objetivo", sa.String(length=120), nullable=True),
            sa.Column("tempo_estimado", sa.String(length=60), nullable=True),
            sa.Column("criado_em", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["dia_id"], ["dia.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade():
    op.drop_table("versao_conteudo")
    op.drop_column("dia", "descricao_visual")

"""Baseline de producao: snapshot do schema que JA EXISTE no Render/PostgreSQL
antes desta serie de migrations. Representa o estado do banco em producao tal
qual estava antes das melhorias (sem dia.descricao_visual e sem versao_conteudo).

EM PRODUCAO (Render, banco ja existe com dados):
    flask db stamp 0001_baseline_producao
    flask db upgrade            # sobe apenas as mudanças incrementais seguintes

EM DEV NOVO (SQLite vazio):
    flask db upgrade            # aplica esta baseline (cria tudo) e as seguintes
"""
from alembic import op
import sqlalchemy as sa


revision = '0001_baseline_producao'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Loja
    op.create_table('loja',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=150), nullable=False),
        sa.Column('cidade', sa.String(length=120), nullable=True),
        sa.Column('instagram', sa.String(length=120), nullable=True),
        sa.Column('whatsapp', sa.String(length=30), nullable=True),
        sa.Column('logo_url', sa.String(length=255), nullable=True),
        sa.Column('estilo', sa.String(length=255), nullable=True),
        sa.Column('publico', sa.String(length=255), nullable=True),
        sa.Column('faixa_preco', sa.String(length=120), nullable=True),
        sa.Column('produtos', sa.Text(), nullable=True),
        sa.Column('tom_de_voz', sa.String(length=255), nullable=True),
        sa.Column('objetivos', sa.Text(), nullable=True),
        sa.Column('diferenciais', sa.Text(), nullable=True),
        sa.Column('dores_do_publico', sa.Text(), nullable=True),
        sa.Column('segmento', sa.String(length=120), nullable=True),
        sa.Column('horario_funcionamento', sa.String(length=120), nullable=True),
        sa.Column('onboarding_concluido', sa.Boolean(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('mes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ano', 'numero', name='uq_mes_ano_numero'),
    )

    op.create_table('semana',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mes_id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('data_inicio', sa.Date(), nullable=True),
        sa.Column('data_fim', sa.Date(), nullable=True),
        sa.Column('promocao', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['mes_id'], ['mes.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('dia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('semana_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('dia_semana', sa.String(length=15), nullable=False),
        sa.Column('ideia_story', sa.Text(), nullable=True),
        sa.Column('ideia_reels', sa.Text(), nullable=True),
        sa.Column('ideia_feed', sa.Text(), nullable=True),
        sa.Column('legenda', sa.Text(), nullable=True),
        sa.Column('cta', sa.String(length=255), nullable=True),
        sa.Column('formato', sa.String(length=80), nullable=True),
        sa.Column('objetivo', sa.String(length=120), nullable=True),
        sa.Column('tempo_estimado', sa.String(length=60), nullable=True),
        sa.Column('tem_post', sa.Boolean(), nullable=True),
        sa.Column('story_feito', sa.Boolean(), nullable=True),
        sa.Column('post_feito', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['semana_id'], ['semana.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('checklist_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dia_id', sa.Integer(), nullable=False),
        sa.Column('texto', sa.String(length=255), nullable=False),
        sa.Column('concluido', sa.Boolean(), nullable=True),
        sa.Column('ordem', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['dia_id'], ['dia.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('ideia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=200), nullable=False),
        sa.Column('tipo', sa.String(length=30), nullable=True),
        sa.Column('conteudo', sa.Text(), nullable=True),
        sa.Column('legenda', sa.Text(), nullable=True),
        sa.Column('cta', sa.String(length=255), nullable=True),
        sa.Column('tags', sa.String(length=255), nullable=True),
        sa.Column('favorito', sa.Boolean(), nullable=True),
        sa.Column('origem', sa.String(length=50), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('concorrente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instagram', sa.String(length=120), nullable=False),
        sa.Column('apelido', sa.String(length=120), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=True),
        sa.Column('observacoes_stories', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('analise_concorrente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('concorrente_id', sa.Integer(), nullable=False),
        sa.Column('dados_brutos', sa.Text(), nullable=True),
        sa.Column('resumo_ia', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['concorrente_id'], ['concorrente.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('insight_semanal',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('semana_id', sa.Integer(), nullable=True),
        sa.Column('texto', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['semana_id'], ['semana.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('insight_semanal')
    op.drop_table('analise_concorrente')
    op.drop_table('concorrente')
    op.drop_table('ideia')
    op.drop_table('checklist_item')
    op.drop_table('dia')
    op.drop_table('semana')
    op.drop_table('mes')
    op.drop_table('loja')

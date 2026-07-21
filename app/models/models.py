from datetime import datetime, timezone
from app.extensions import db


class Loja(db.Model):
    """Perfil da loja - preenchido no primeiro uso (onboarding)."""
    __tablename__ = "loja"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cidade = db.Column(db.String(120))
    instagram = db.Column(db.String(120))
    whatsapp = db.Column(db.String(30))
    logo_url = db.Column(db.String(255))
    estilo = db.Column(db.String(255))          # ex: casual, festa, plus size...
    publico = db.Column(db.String(255))          # ex: jovens 18-30 anos
    faixa_preco = db.Column(db.String(120))       # ex: R$ 79 a R$ 250
    produtos = db.Column(db.Text)                 # o que a loja vende
    tom_de_voz = db.Column(db.String(255))        # ex: descontraído, elegante
    objetivos = db.Column(db.Text)                # ex: vender mais, ganhar seguidores
    diferenciais = db.Column(db.Text)             # ex: curadoria premium, fabricação própria
    dores_do_publico = db.Column(db.Text)         # ex: não tem tempo, não sabe combinar
    segmento = db.Column(db.String(120), default="Moda Feminina")
    horario_funcionamento = db.Column(db.String(120))
    onboarding_concluido = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Mes(db.Model):
    __tablename__ = "mes"

    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False)
    numero = db.Column(db.Integer, nullable=False)  # 1-12
    nome = db.Column(db.String(30), nullable=False)  # "Julho"

    semanas = db.relationship("Semana", backref="mes", cascade="all, delete-orphan", order_by="Semana.numero")

    __table_args__ = (db.UniqueConstraint("ano", "numero", name="uq_mes_ano_numero"),)


class Semana(db.Model):
    __tablename__ = "semana"

    id = db.Column(db.Integer, primary_key=True)
    mes_id = db.Column(db.Integer, db.ForeignKey("mes.id"), nullable=False)
    numero = db.Column(db.Integer, nullable=False)  # 1 a 5
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    promocao = db.Column(db.Text)  # promoção/ação especial que a lojista quer destacar na semana

    dias = db.relationship("Dia", backref="semana", cascade="all, delete-orphan", order_by="Dia.data")


class Dia(db.Model):
    __tablename__ = "dia"

    id = db.Column(db.Integer, primary_key=True)
    semana_id = db.Column(db.Integer, db.ForeignKey("semana.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    dia_semana = db.Column(db.String(15), nullable=False)  # segunda, terca...

    # Conteúdo do dia
    ideia_story = db.Column(db.Text)
    ideia_reels = db.Column(db.Text)
    ideia_feed = db.Column(db.Text)
    legenda = db.Column(db.Text)
    descricao_visual = db.Column(db.Text)       # cena concreta da foto/vídeo para a lojista
    cta = db.Column(db.String(255))
    formato = db.Column(db.String(80))          # foto, vídeo, carrossel, reels...
    objetivo = db.Column(db.String(120))         # vender, engajar, educar...
    tempo_estimado = db.Column(db.String(60))    # "20 minutos"

    tem_post = db.Column(db.Boolean, default=False)
    story_feito = db.Column(db.Boolean, default=False)
    post_feito = db.Column(db.Boolean, default=False)

    checklist_items = db.relationship("ChecklistItem", backref="dia", cascade="all, delete-orphan")
    versoes = db.relationship(
        "VersaoConteudo",
        backref="dia",
        cascade="all, delete-orphan",
        order_by="VersaoConteudo.criado_em.desc()",
    )

    @property
    def dia_completo(self):
        if not self.checklist_items:
            return False
        return all(item.concluido for item in self.checklist_items)


class ChecklistItem(db.Model):
    __tablename__ = "checklist_item"

    id = db.Column(db.Integer, primary_key=True)
    dia_id = db.Column(db.Integer, db.ForeignKey("dia.id"), nullable=False)
    texto = db.Column(db.String(255), nullable=False)
    concluido = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer, default=0)


class Ideia(db.Model):
    """Banco de Ideias: ideias salvas, reutilizáveis, pesquisáveis e favoritáveis."""
    __tablename__ = "ideia"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(30))               # story, reels, feed
    conteudo = db.Column(db.Text)
    legenda = db.Column(db.Text)
    cta = db.Column(db.String(255))
    tags = db.Column(db.String(255))               # separado por vírgula
    favorito = db.Column(db.Boolean, default=False)
    origem = db.Column(db.String(50), default="ia")  # ia, manual, data_comemorativa
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Concorrente(db.Model):
    __tablename__ = "concorrente"

    id = db.Column(db.Integer, primary_key=True)
    instagram = db.Column(db.String(120), nullable=False)  # @perfil
    apelido = db.Column(db.String(120))
    ativo = db.Column(db.Boolean, default=True)
    observacoes_stories = db.Column(db.Text)  # anotação manual (stories não são coletáveis)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    analises = db.relationship("AnaliseConcorrente", backref="concorrente", cascade="all, delete-orphan")


class AnaliseConcorrente(db.Model):
    __tablename__ = "analise_concorrente"

    id = db.Column(db.Integer, primary_key=True)
    concorrente_id = db.Column(db.Integer, db.ForeignKey("concorrente.id"), nullable=False)
    dados_brutos = db.Column(db.Text)     # JSON com o que foi coletado (posts públicos)
    resumo_ia = db.Column(db.Text)        # texto gerado pela IA (pontos fortes, oportunidades...)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class InsightSemanal(db.Model):
    """Análises automáticas geradas semanalmente pela IA sobre o próprio desempenho."""
    __tablename__ = "insight_semanal"

    id = db.Column(db.Integer, primary_key=True)
    semana_id = db.Column(db.Integer, db.ForeignKey("semana.id"))
    texto = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class VersaoConteudo(db.Model):
    """Histórico de versões de um conteúdo (story/reels/feed) dentro de um dia.

    Toda vez que a lojista regenera uma ideia (botão "Gerar nova ideia"), a versão
    atual é preservada aqui ANTES de ser sobrescrita - evitando perder conteúdo bom
    que foi substituído acidentalmente. Vizualizável na tela do dia e restaurável."""
    __tablename__ = "versao_conteudo"

    id = db.Column(db.Integer, primary_key=True)
    dia_id = db.Column(db.Integer, db.ForeignKey("dia.id"), nullable=False)
    tipo = db.Column(db.String(15), nullable=False)  # story | reels | feed
    conteudo = db.Column(db.Text)                       # texto da ideia (ideia_story/reels/feed)
    descricao_visual = db.Column(db.Text)
    legenda = db.Column(db.Text)
    cta = db.Column(db.String(255))
    formato = db.Column(db.String(80))
    objetivo = db.Column(db.String(120))
    tempo_estimado = db.Column(db.String(60))
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

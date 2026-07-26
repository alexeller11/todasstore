import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    # SECRET_KEY must be provided via env in production; raise if missing
    SECRET_KEY = os.environ["SECRET_KEY"]

    # Banco de dados: usa PostgreSQL no Render (DATABASE_URL) ou SQLite localmente
    _database_url = os.environ.get("DATABASE_URL", "")
    if _database_url.startswith("postgres://"):
        # Render entrega a URL no formato antigo; SQLAlchemy exige "postgresql://"
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _database_url or f"sqlite:///{os.path.join(basedir, 'instance', 'todasstore.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # IA - Groq
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL_PRINCIPAL = os.environ.get("GROQ_MODEL_PRINCIPAL", "llama-3.3-70b-versatile")
    GROQ_MODEL_ALTERNATIVO = os.environ.get("GROQ_MODEL_ALTERNATIVO", "qwen/qwen3-32b")

    # Dias da semana padrão (usados no planejamento automático)
    DIAS_SEMANA = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]

    # Checklist padrão para cada dia (editável depois pela usuária)
    CHECKLIST_PADRAO = [
        "Tirar fotos",
        "Gravar vídeos",
        "Editar vídeo",
        "Publicar Story",
        "Publicar Feed",
        "Publicar Reels",
        "Responder comentários",
        "Responder Direct",
        "Mostrar bastidores",
        "Mostrar novidade",
        "Mostrar look",
        "Mostrar promoção",
    ]

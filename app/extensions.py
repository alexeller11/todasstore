from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()

# Limita a quantidade de gerações por IA por pessoa/IP - o app não tem login,
# então isso é o que evita alguém (ou um bot) esgotar a cota gratuita da
# Groq só de ficar clicando/repetindo requisições. Guarda os contadores em
# memória (não precisa de Redis) - funciona bem porque o app roda com 1
# worker do gunicorn (ver render.yaml).
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

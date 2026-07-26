"""ai_content Blueprint – generate Instagram caption & hashtags.

Endpoints:
    POST /ai/content/from-image – receive an image (multipart) and return JSON with
        {"legenda": "...", "hashtags": ["#...", ...]}
    POST /ai/content/from-text – receive a short text/theme and generate a content
        idea (legenda, cta, formato, etc.) using the existing AI service.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import base64

from app.ai.ai_service import gerar_json

bp = Blueprint('ai_content', __name__, url_prefix='/ai/content')

@bp.route('/from-image', methods=['POST'])
def from_image():
    """Generate caption and hashtags from an uploaded image.
    The image is read, encoded in base64 and sent to the Groq model via the
    generic ``gerar_json`` helper, using a prompt that asks for a marketing copy.
    """
    file = request.files.get('image')
    if not file:
        return jsonify({"ok": False, "erro": "imagem ausente"}), 400

    filename = secure_filename(file.filename)
    tmp_dir = os.path.join(current_app.instance_path, 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, filename)
    file.save(tmp_path)

    try:
        with open(tmp_path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode()
        system_prompt = (
            "Você é um assistente de marketing especializado em moda feminina. "
            "Com base na imagem fornecida (base64), gere uma legenda criativa para Instagram, "
            "inclua de 5 a 7 hashtags relevantes e sugira um CTA. "
            "Retorne JSON no formato: {\"legenda\": ..., \"hashtags\": [...]}"
        )
        user_prompt = f"<imagem_base64>{img_b64}</imagem_base64>"
        result = gerar_json(system_prompt, user_prompt)
        return jsonify({"ok": True, "data": result})
    finally:
        # Clean up the temporary file
        try:
            os.remove(tmp_path)
        except Exception:
            pass

@bp.route('/from-text', methods=['POST'])
def from_text():
    """Generate a full content idea from a short text/theme.
    Expected JSON body: {"tema": "..."}
    Returns the same structure used by the planner (legenda, cta, formato, etc.).
    """
    data = request.get_json(silent=True) or {}
    tema = data.get('tema', '')
    if not tema:
        return jsonify({"ok": False, "erro": "tema ausente"}), 400

    system_prompt = (
        "Você é um assistente de marketing para uma loja de roupas. "
        "Com base no tema fornecido, gere uma sugestão de conteúdo para Instagram, "
        "incluindo legenda, hashtags, CTA, formato (story/reels/feed) e sugestão visual. "
        "Retorne JSON com as chaves: legenda, hashtags, cta, formato, visual (descrição)."
    )
    user_prompt = tema
    result = gerar_json(system_prompt, user_prompt)
    return jsonify({"ok": True, "data": result})

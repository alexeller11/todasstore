"""Tests for the AI content generation endpoints.
We mock the Groq call so no external API is hit.
"""
import io
import json
from unittest.mock import patch

from app import create_app


def _app():
    app = create_app()
    app.config["TESTING"] = True
    return app


def test_from_image_success():
    app = _app()
    client = app.test_client()
    # Mock the Groq call that gera_json ultimately uses
    mock_response = {"legenda": "Look incrível!", "hashtags": ["#moda", "#estilo"]}
    with patch('app.ai.ai_service._chamar_modelo', return_value=json.dumps(mock_response)):
        data = {
            'image': (io.BytesIO(b'fake-image-data'), 'test.jpg')
        }
        resp = client.post('/ai/content/from-image', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["ok"] is True
        assert payload["data"]["legenda"] == "Look incrível!"
        assert payload["data"]["hashtags"] == ["#moda", "#estilo"]


def test_from_text_success():
    app = _app()
    client = app.test_client()
    mock_response = {
        "legenda": "Nova coleção chegou!",
        "hashtags": ["#novacolecao"],
        "cta": "Confira agora",
        "formato": "feed",
        "visual": "foto de estação"
    }
    # gerar_json wraps _chamar_modelo and parses JSON, so we mock the lower level
    with patch('app.ai.ai_service._chamar_modelo', return_value=json.dumps(mock_response)):
        resp = client.post('/ai/content/from-text', json={"tema": "nova coleção"})
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["ok"] is True
        assert payload["data"]["legenda"] == "Nova coleção chegou!"
        assert payload["data"]["cta"] == "Confira agora"

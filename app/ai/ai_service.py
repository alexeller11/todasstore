"""
ai_service.py
Camada única de comunicação com a Groq API.
Todo o resto do sistema fala com a IA através deste serviço,
nunca diretamente - assim é fácil trocar de modelo/provedor no futuro.
"""
import json
import os
from groq import Groq
from flask import current_app


def _get_client():
    api_key = current_app.config.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "A chave da IA (GROQ_API_KEY) não está configurada! Por favor, adicione-a no arquivo .env."
        )
    return Groq(api_key=api_key, max_retries=2, timeout=20.0)


def _chamar_modelo(mensagens, json_mode=True, temperatura=0.8):
    """Chama a Groq, com fallback automático para o modelo alternativo se o principal falhar."""
    client = _get_client()
    modelos = [
        current_app.config.get("GROQ_MODEL_PRINCIPAL", "llama-3.3-70b-versatile"),
        current_app.config.get("GROQ_MODEL_ALTERNATIVO", "qwen/qwen2.5-32b-instruct"),
    ]

    ultimo_erro = None
    for modelo in modelos:
        try:
            kwargs = dict(
                model=modelo,
                messages=mensagens,
                temperature=temperatura,
                max_tokens=2000,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as e:
            current_app.logger.warning(f"Erro ao chamar modelo {modelo}: {e}")
            ultimo_erro = e
            continue
    
    current_app.logger.error(f"Todos os modelos da Groq falharam. Último erro: {ultimo_erro}")
    raise RuntimeError("Nossa IA está sobrecarregada ou indisponível no momento. Por favor, tente novamente em alguns instantes.")


def gerar_json(system_prompt, user_prompt, temperatura=0.8):
    """Pede à IA uma resposta estritamente em JSON e já devolve o dict pronto."""
    mensagens = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    texto = _chamar_modelo(mensagens, json_mode=True, temperatura=temperatura)
    texto_limpo = texto.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(texto_limpo)
    except json.JSONDecodeError:
        # tenta achar o primeiro { e o último } como rede de segurança
        inicio = texto_limpo.find("{")
        fim = texto_limpo.rfind("}")
        if inicio != -1 and fim != -1:
            return json.loads(texto_limpo[inicio:fim + 1])
        raise RuntimeError("A IA respondeu em um formato inesperado. Tente novamente.")


def gerar_texto(system_prompt, user_prompt, temperatura=0.7):
    """Pede à IA uma resposta em texto livre (usado para insights, análises)."""
    mensagens = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return _chamar_modelo(mensagens, json_mode=False, temperatura=temperatura)

"""
instagram_service.py

IMPORTANTE - LEIA COM ATENÇÃO:
O Instagram não oferece uma API gratuita e oficial para consultar perfis de terceiros,
e bloqueia ativamente tentativas automatizadas de leitura de suas páginas (login wall,
carregamento via JavaScript, limites de taxa). Por isso, este serviço tenta uma leitura
"best effort" da página pública do perfil (meta tags e dados básicos) e, quando não
consegue, orienta a usuária a preencher os dados manualmente.

Stories nunca podem ser coletados automaticamente (eles somem em 24h e não existem em
nenhuma página pública indexável) - por isso o sistema sempre trata isso como campo manual.

Nenhuma credencial de login é usada aqui: apenas leitura de página pública, sem burlar
nenhum tipo de autenticação ou limite de acesso.
"""
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def coletar_dados_publicos(usuario_instagram):
    """
    Tenta coletar dados básicos e públicos do perfil (nome, bio, nº de posts/seguidores
    quando disponíveis nas meta tags). Retorna um dicionário sempre - se a coleta falhar,
    devolve disponivel=False e um motivo em linguagem simples.
    """
    usuario = usuario_instagram.strip().lstrip("@")
    url = f"https://www.instagram.com/{usuario}/"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return _falha("O Instagram bloqueou a consulta automática deste perfil.")

        soup = BeautifulSoup(resp.text, "html.parser")
        meta_desc = soup.find("meta", property="og:description")
        meta_title = soup.find("meta", property="og:title")

        if not meta_desc:
            return _falha(
                "Não foi possível ler os dados públicos automaticamente "
                "(o Instagram exige login para ver esse conteúdo)."
            )

        descricao = meta_desc.get("content", "")
        titulo = meta_title.get("content", "") if meta_title else ""

        return {
            "disponivel": True,
            "usuario": usuario,
            "titulo": titulo,
            "descricao_publica": descricao,
            "motivo_indisponivel": None,
        }
    except requests.RequestException:
        return _falha("Não foi possível conectar ao Instagram agora. Tente novamente mais tarde.")


def _falha(motivo):
    return {
        "disponivel": False,
        "usuario": None,
        "titulo": None,
        "descricao_publica": None,
        "motivo_indisponivel": motivo,
    }


def montar_texto_dados_para_ia(dados_publicos, observacoes_manuais):
    """
    Monta o texto que será enviado à IA, combinando o que foi coletado automaticamente
    (quando disponível) com o que a lojista registrou manualmente sobre o concorrente.
    """
    if dados_publicos.get("disponivel"):
        base = (
            f"Descrição pública do perfil: {dados_publicos.get('descricao_publica')}\n"
            "Observação: a coleta automática de posts individuais (legendas, hashtags, "
            "curtidas) não é garantida pelo Instagram e pode estar limitada nesta consulta."
        )
    else:
        base = (
            "A coleta automática não teve dados suficientes desta vez "
            f"({dados_publicos.get('motivo_indisponivel')}). "
            "A análise abaixo se baseia principalmente nas observações manuais registradas."
        )

    if observacoes_manuais:
        base += f"\n\nObservações manuais registradas pela lojista:\n{observacoes_manuais}"

    return base

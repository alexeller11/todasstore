# -*- coding: utf-8 -*-
"""campaign_ideas.py

For a boutique clothing store, a handful of tried‑and‑tested marketing campaigns are
provided here as simple static data. They can be served via an API endpoint or
imported by the UI to inspire the user when planning the weekly content.

Each entry contains:
- ``nome`` – a short name for the campaign.
- ``descricao`` – a brief explanation of the concept.
- ``exemplo`` – an example of a post/Story/Reels that could be used.
- ``dicas`` – practical tips for execution.
"""

from typing import List, Dict


def get_successful_campaigns() -> List[Dict[str, str]]:
    """Return a list of successful campaign ideas for a fashion boutique.

    The list is static – in a real product you could load it from a DB or a
    remote CMS, but keeping it in‑code satisfies the requirement of providing
    ready‑to‑use inspiration.
    """
    return [
        {
            "nome": "Look do Dia",
            "descricao": "Mostre um outfit completo todos os dias, destacando uma peça‑chave da coleção.",
            "exemplo": "Story com foto do look + swipe‑up para a página do produto.",
            "dicas": "Use luz natural, inclua a legenda com hashtags de estilo e CTA para comprar."
        },
        {
            "nome": "Desafio de 7 Dias",
            "descricao": "Proponha um desafio de moda (ex.: #7DiasDeEstilo) e incentive seguidores a postar usando a hashtag.",
            "exemplo": "Reels mostrando diferentes combinações da mesma peça ao longo da semana.",
            "dicas": "Ofereça um desconto ou brinde para quem participar e marcar a loja."
        },
        {
            "nome": "Campanha de Lançamento de Coleção",
            "descricao": "Crie suspense com teasers e revele a nova coleção em um live ou carrossel.",
            "exemplo": "Post carrossel com close‑ups dos detalhes e um vídeo 'behind the scenes'.",
            "dicas": "Anuncie a data de disponibilidade e use contagem regressiva nos Stories."
        },
        {
            "nome": "Sorteio de Kit de Looks",
            "descricao": "Peça ao seguidor que siga, curta e marque amigos para concorrer a um kit completo.",
            "exemplo": "Post com foto do kit, regras na legenda e um Stories ressaltando o prazo.",
            "dicas": "Defina regras claras e anuncie o vencedor em tempo real para criar engajamento."
        },
        {
            "nome": "Campanha de Influencer Local",
            "descricao": "Parceria com micro‑influencers da região para que usem peças da loja e criem conteúdo.",
            "exemplo": "Reels do influencer usando a roupa, tagando a loja e oferecendo código de desconto.",
            "dicas": "Escolha influenciadores cujo público coincida com o seu segmento e monitore métricas."
        },
        {
            "nome": "Flash Sale Relâmpago",
            "descricao": "Desconto de poucas horas em um produto específico, divulgado nos Stories.",
            "exemplo": "Story com contagem regressiva, link direto ao produto e 'use o código FLASH20'.",
            "dicas": "Crie urgência com horário limitado e destaque a economia."
        }
    ]

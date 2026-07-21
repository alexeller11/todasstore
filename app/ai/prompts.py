"""
prompts.py
Todos os textos enviados à IA ficam centralizados aqui.
Isso facilita ajustar o "jeito de falar" da assistente sem mexer na lógica do sistema.
"""


def contexto_loja(loja):
    """Monta um bloco de texto com o perfil da loja, usado em quase todos os prompts."""
    if not loja:
        return "Loja de roupas femininas (perfil ainda não configurado)."
    return f"""
Nome da loja: {loja.nome}
Cidade: {loja.cidade or "não informado"}
Estilo da loja: {loja.estilo or "não informado"}
Público-alvo: {loja.publico or "não informado"}
Faixa de preço: {loja.faixa_preco or "não informado"}
Produtos vendidos: {loja.produtos or "não informado"}
Tom de voz da marca: {loja.tom_de_voz or "descontraído e acolhedor"}
Objetivos da loja: {loja.objetivos or "vender mais e crescer no Instagram"}
""".strip()


SYSTEM_MARKETING = """
Você é uma consultora especialista em moda feminina e varejo de roupas no Brasil, com anos de
experiência ajudando lojas físicas e de Instagram a vender mais. Você entende profundamente de:
- Tendências de moda por estação (cores, tecidos, modelagens, o que "vende" em cada época do ano)
- Como combinar peças, criar looks e sugerir composições de venda cruzada (ex: vestido + acessório)
- Comportamento de compra de roupa feminina (impulso, prova social, urgência, sazonalidade)
- Linguagem e visual que engajam no Instagram especificamente para moda (looks, provador, bastidores
  de costura/estoque, "combina com o quê", tamanhos e caimento)
- Datas de calendário de moda: liquidações de coleção, trocas de estação, datas comemorativas que
  geram vendas de roupa (Dia das Mães, Namorados, festas de fim de ano, etc)

Você SEMPRE usa o perfil real da loja (estilo, público-alvo, faixa de preço, produtos, tom de voz)
para tornar cada ideia específica DAQUELA loja - nunca escreve algo genérico que serviria pra
qualquer loja de roupa. Você fala de forma simples, prática e motivadora, como uma amiga que
entende do assunto, sem jargões técnicos de marketing.

Sempre responde SOMENTE em JSON válido, no formato exato pedido, sem texto antes ou depois, sem
comentários e sem markdown.
""".strip()

SYSTEM_ANALISE = """
Você é uma consultora de moda feminina e varejo, especializada em analisar o Instagram de
concorrentes de lojas de roupa no Brasil. Você entende de tendências de moda por estação,
estratégias de venda de roupa (looks, combinações, gatilhos de urgência e prova social) e de
como o algoritmo do Instagram favorece conteúdo de moda. Analisa dados e devolve insights
práticos e acionáveis, específicos para o contexto de moda feminina, em português, de forma
simples e direta, sem jargões técnicos.
""".strip()


def prompt_planejamento_semana(loja, data_inicio, datas_comemorativas=None, promocao=None, estacao=None):
    datas_txt = ""
    if datas_comemorativas:
        datas_txt = "Datas comemorativas nesta semana: " + ", ".join(datas_comemorativas) + "."

    estacao_txt = f"Estação do ano no Brasil nesta semana: {estacao}." if estacao else ""

    promocao_txt = ""
    if promocao:
        promocao_txt = f"""
Promoção/ação especial desta semana (MUITO IMPORTANTE): "{promocao}"
Essa promoção deve aparecer de forma natural em pelo menos 2 ou 3 dias da semana
(stories e/ou posts), sem exagerar e sem parecer forçado nos outros dias.
""".strip()

    user_prompt = f"""
Perfil da loja:
{contexto_loja(loja)}

Crie o planejamento de conteúdo do Instagram para UMA semana completa, começando em {data_inicio}.
{estacao_txt}
{datas_txt}
{promocao_txt}

Regras obrigatórias:
- Um Story para CADA um dos 7 dias (segunda a domingo).
- Exatamente 3 dias da semana devem ter também um Post completo (feed ou reels), bem distribuídos
  (não em dias seguidos, se possível).
- Linguagem simples, pronta para a lojista usar sem editar.
- As legendas devem soar humanas, com emojis com moderação, nunca robóticas.
- NUNCA sugira peças, looks ou cores incompatíveis com a estação do ano informada acima
  (ex: não sugira "looks de verão" ou "peças leves" se a estação for Inverno).
- Evite ideias genéricas e clichês ("mostre os mais vendidos", "poste um look do dia"). Seja
  específica: cite peça, cor, ocasião ou tendência real da estação em cada dia.
- Use o estilo, o público-alvo e os produtos DESSA loja (informados acima) para tornar cada
  ideia única dela - não escreva algo que serviria pra qualquer loja de roupa.

Devolva APENAS este JSON (sem nenhum texto fora dele):
{{
  "dias": {{
    "segunda": {{"tem_post": true|false, "ideia_story": "...", "ideia_reels": "..." (ou null), "ideia_feed": "..." (ou null), "legenda": "..." (ou null), "cta": "..." (ou null), "formato": "foto|video|carrossel|reels" (ou null), "objetivo": "vender|engajar|educar|relacionamento", "tempo_estimado": "20 minutos"}},
    "terca": {{...}},
    "quarta": {{...}},
    "quinta": {{...}},
    "sexta": {{...}},
    "sabado": {{...}},
    "domingo": {{...}}
  }}
}}
""".strip()
    return SYSTEM_MARKETING, user_prompt


def prompt_nova_ideia_dia(loja, dia_semana, tipo, data=None, estacao=None, datas_proximas=None, contexto_extra=""):
    campo_ideia = {"story": "ideia_story", "reels": "ideia_reels", "feed": "ideia_feed"}.get(tipo, "ideia_story")

    contexto_temporal = ""
    if data:
        contexto_temporal += f"Data: {data} ({dia_semana}).\n"
    if estacao:
        contexto_temporal += f"Estação do ano no Brasil nesta data: {estacao}.\n"
    if datas_proximas:
        contexto_temporal += "Datas comemorativas próximas: " + ", ".join(datas_proximas) + ".\n"

    user_prompt = f"""
Perfil da loja:
{contexto_loja(loja)}

{contexto_temporal}
Gere UMA nova ideia de conteúdo do tipo "{tipo}", para o dia: {dia_semana}.
{contexto_extra}

IMPORTANTE:
- O campo "{campo_ideia}" é OBRIGATÓRIO e precisa ter uma frase real e específica
  descrevendo a ideia (nunca deixe vazio, nulo ou genérico como "ideia de {tipo}").
- Leve em conta a estação do ano e as datas comemorativas próximas informadas acima -
  NUNCA sugira peças ou looks incompatíveis com o clima da estação atual (ex: não sugira
  "looks de verão" se a estação for Inverno).
- Evite ideias genéricas e clichês ("mostre os mais vendidos", "poste um look do dia").
  Seja específica: cite uma peça, cor, ocasião, tendência da estação ou gatilho real de venda.
- Use o estilo, o público-alvo e os produtos DESSA loja (informados acima) para tornar a ideia
  única dela - não escreva algo que serviria pra qualquer loja de roupa.
- Se houver uma data comemorativa próxima relevante para moda feminina, aproveite a deixa
  quando fizer sentido.

Devolva APENAS este JSON, preenchendo TODOS os campos abaixo com conteúdo real:
{{
  "{campo_ideia}": "descrição específica e pronta de usar da ideia de {tipo}",
  "legenda": "legenda pronta para usar na publicação",
  "cta": "chamada para ação curta",
  "formato": "foto|video|carrossel|reels",
  "objetivo": "vender|engajar|educar|relacionamento",
  "tempo_estimado": "15 minutos"
}}
""".strip()
    return SYSTEM_MARKETING, user_prompt


def prompt_conteudo_data_comemorativa(loja, nome_data, data_iso):
    user_prompt = f"""
Perfil da loja:
{contexto_loja(loja)}

Crie 3 ideias de conteúdo especial para a data comemorativa "{nome_data}" (dia {data_iso}).
Pense em ações que ajudem a vender mais aproveitando a data.

Devolva APENAS este JSON:
{{
  "ideias": [
    {{"titulo": "...", "tipo": "story|reels|feed", "conteudo": "...", "legenda": "...", "cta": "..."}},
    {{"titulo": "...", "tipo": "story|reels|feed", "conteudo": "...", "legenda": "...", "cta": "..."}},
    {{"titulo": "...", "tipo": "story|reels|feed", "conteudo": "...", "legenda": "...", "cta": "..."}}
  ]
}}
""".strip()
    return SYSTEM_MARKETING, user_prompt


def prompt_analise_concorrente(loja, concorrente, dados_coletados, observacoes_stories):
    user_prompt = f"""
Perfil da minha loja:
{contexto_loja(loja)}

Estou analisando o concorrente @{concorrente.instagram} para melhorar minha estratégia,
sem copiar o conteúdo dele.

Dados públicos coletados sobre as publicações recentes dele:
{dados_coletados}

Observações manuais sobre os Stories dele (registradas pela lojista, já que Stories não
podem ser coletados automaticamente):
{observacoes_stories or "nenhuma observação registrada ainda"}

Responda em português, de forma simples e organizada, com estes tópicos:
1. O que esse concorrente faz bem
2. O que ele repete demais (padrões, possíveis pontos fracos)
3. Oportunidades que ele está deixando passar
4. Que tipo de conteúdo a MINHA loja pode produzir para se destacar
5. 3 sugestões de conteúdos inéditos, inspirados no mercado, mas SEM copiar o concorrente
""".strip()
    return SYSTEM_ANALISE, user_prompt


def prompt_insight_semanal(loja, resumo_semana):
    user_prompt = f"""
Perfil da loja:
{contexto_loja(loja)}

Aqui está um resumo do que foi publicado essa semana:
{resumo_semana}

Analise e dê um retorno curto e gentil (máximo 5 frases), em português simples, destacando:
- Se houve equilíbrio entre posts de venda e posts de relacionamento/bastidores
- Se a diversidade de formatos (foto, vídeo, carrossel) foi boa
- Uma sugestão prática e específica para a próxima semana

Fale diretamente com a lojista, como uma consultora amiga, sem jargões técnicos.
""".strip()
    return SYSTEM_ANALISE, user_prompt

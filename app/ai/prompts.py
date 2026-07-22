"""
prompts.py
Todos os textos enviados à IA ficam centralizados aqui.
Isso facilita ajustar o "jeito de falar" da assistente sem mexer na lógica do sistema.
"""


def contexto_loja(loja):
    """Monta um bloco de texto com o perfil da loja, usado em quase todos os prompts.

    Se diferenciais ou dores_do_publico estiverem vazios (comum em lojas que
    ainda nao preencheram o perfil completo), orienta a IA a inferir a partir
    dos outros campos - evitando que a saida fique superficial por falta de
    informacao especifica. Em vez de simplesmente escrever "nao informado",
    sinalizamos que ela deve INFERIR e usar de forma concreta."""
    if not loja:
        return "Loja de roupas femininas (perfil ainda nao configurado)."

    nome = loja.nome or "Loja de moda feminina"
    estilo = loja.estilo or "moda feminina"
    publico = loja.publico or "mulheres"
    faixa = loja.faixa_preco or "preco acessivel"
    produtos = loja.produtos or "roupas femininas"
    tom = loja.tom_de_voz or "descontrado e acolhedor"
    objetivos = loja.objetivos or "vender mais e crescer no Instagram"

    if loja.diferenciais and loja.dores_do_publico:
        # caso ideal: lojista preencheu tudo
        diferenciais_txt = loja.diferenciais
        dores_txt = loja.dores_do_publico
        nota_ia = ""
    else:
        # perfil incompleto: pede inferencia e avisa sobre o risco de generico
        diferenciais_txt = loja.diferenciais or "(NAO INFORMADO - INFIRA a partir do estilo, faixa de preco e produtos; NAO use cliches)"
        dores_txt = loja.dores_do_publico or "(NAO INFORMADO - INFIRA dores reais que esse publico costuma ter com moda; NAO use dores genericas como 'nao sabe o que vestir')"
        nota_ia = (
            "\n\nATENCAO: a lojista ainda nao preencheu os campos de "
            "diferenciais e dores do publico. Voce precisa INFERIR a partir "
            "do que esta acima (estilo, publico, faixa de preco, produtos) "
            "para gerar conteudo especifico. PROIBIDO cair em frases "
            "genericas como 'novidades incriveis' ou 'looks para todas as "
            "ocasioes'. Escolha uma peca concreta e explore UM detalhe "
            "especifico dela (tecido, modelagem, ocasiao)."
        )

    return f"""
Nome da loja: {nome}
Cidade: {loja.cidade or "nao informado"}
Estilo da loja: {estilo}
Diferenciais da marca: {diferenciais_txt}
Publico-alvo: {publico}
Principais dores do publico: {dores_txt}
Faixa de preco: {faixa}
Produtos vendidos: {produtos}
Tom de voz da marca: {tom}
Objetivos da loja: {objetivos}{nota_ia}
""".strip()


SYSTEM_MARKETING = """
Você é uma consultora de alta conversão especialista em moda feminina e varejo no Brasil, focada em gerar vendas reais no Instagram.
Você entende profundamente de:
- Gatilhos Mentais (Escassez, Urgência, Prova Social, Pertencimento, Exclusividade) aplicados à moda.
- Copywriting focado em vendas, especialmente a fórmula PAS (Problema - Agitação - Solução), focando na transformação e na dor do cliente.
- Tendências de moda por estação, truques de styling (color block, monocromático, etc) e o que "vende" em cada época.
- Comportamento de compra e funil de vendas (AIDA: Atenção, Interesse, Desejo, Ação).

Você SEMPRE usa o perfil real da loja (especialmente seus diferenciais e dores do público) para tornar cada ideia específica DAQUELA loja.
Sua linguagem é magnética, sofisticada mas acessível, como uma estrategista de marca conversando com a cliente ideal.

REGRAS DE QUALIDADE (são OBRIGATÓRIAS e serão avaliadas):
- A legenda de feed/reels deve ter ENTRE 80 E 220 palavras. Nem curta demais (não entrega valor), nem longa demais (perde atenção). Em stories, a legenda pode ser mais curta (30 a 90 palavras), mas ainda específica.
- NUNCA devolva conteúdo genérico ("venha conferir", "novidades incríveis"). Sempre cite um produto/estilo/reação da cliente real da loja em questão.
- Para todo feed/reels, preencha o campo "descricao_visual" com a cena concreta da imagem/vídeo (ex: modelo + peça + ângulo + cenário), para a lojista saber O QUE fotografar/gravar.
- Aplique a fórmula PAS (Problema - Agitação - Solução) na legenda sempre que o objetivo for venda ou engajamento.

PROIBIDO:
- Frases clichês de vendedor antigo ("Venha conferir a nova coleção", "Looks para todas as ocasiões", "Corre pra garantir").
- Abordagens frias. Cada legenda deve contar uma micro-história ou resolver um problema real da mulher.

Sempre responde SOMENTE em JSON válido, no formato exato pedido, sem texto antes ou depois, sem markdown.
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
- Exatamente 3 dias da semana devem ter também um Post completo (feed ou reels), bem distribuídos.
- Aplique Eixos de Conteúdo: tenha pelo menos 1 dia focado em Educar (ex: truque de styling), 1 dia de Bastidores/Relacionamento e os demais focados em Vendas.
- Nas legendas de feed/reels, utilize a fórmula PAS (Problema - Agitação - Solução) para prender a atenção da cliente.
- NUNCA sugira peças, looks ou cores incompatíveis com a estação do ano ({estacao}).
- Use os diferenciais da loja e as dores do público (informados acima) para tornar cada ideia magnética e altamente conversiva.
- Adicione 3 a 5 hashtags estratégicas no final de CADA legenda.

Devolva APENAS este JSON (sem nenhum texto fora dele):
{{
  "dias": {{
    "segunda": {{"tem_post": true|false, "ideia_story": "...", "ideia_reels": "..." (ou null), "ideia_feed": "..." (ou null), "legenda": "texto com PAS + hashtags, 80-220 palavras..." (ou null), "descricao_visual": "cena concreta da foto/video..." (ou null), "cta": "..." (ou null), "formato": "foto|video|carrossel|reels" (ou null), "objetivo": "vender|engajar|educar|relacionamento", "tempo_estimado": "20 minutos"}},
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


def prompt_nova_ideia_dia(loja, dia_semana, tipo, data=None, estacao=None, datas_proximas=None, promocao=None, contexto_extra=""):
    campo_ideia = {"story": "ideia_story", "reels": "ideia_reels", "feed": "ideia_feed"}.get(tipo, "ideia_story")

    contexto_temporal = ""
    if data:
        contexto_temporal += f"Data: {data} ({dia_semana}).\n"
    if estacao:
        contexto_temporal += f"Estação do ano no Brasil nesta data: {estacao}.\n"
    if datas_proximas:
        contexto_temporal += "Datas comemorativas próximas: " + ", ".join(datas_proximas) + ".\n"

    promocao_txt = ""
    if promocao:
        promocao_txt = f"""
Promoção/ação especial da SEMANA deste dia (MUITO IMPORTANTE): "{promocao}"
Encaixe essa promoção de forma natural na ideia de {tipo} se fizer sentido, sem parecer forçado.
""".strip()

    user_prompt = f"""
Perfil da loja:
{contexto_loja(loja)}

{contexto_temporal}
{promocao_txt}
Gere UMA nova ideia de conteúdo do tipo "{tipo}", para o dia: {dia_semana}.
{contexto_extra}

IMPORTANTE:
- O campo "{campo_ideia}" é OBRIGATÓRIO e precisa ter uma frase real e específica, citando produto/peça/reação da cliente.
- Aplique a fórmula de copywriting PAS (Problema - Agitação - Solução) na legenda se o objetivo for venda ou engajamento, conectando com as dores do público.
- A legenda precisa ter ENTRE 80 E 220 palavras (se for story: 30 a 90 palavras). Não seja superficial.
- Inclua de 3 a 5 hashtags estratégicas no final da legenda.
- O campo "descricao_visual" descreve a CENA concreta (peça + ângulo + cenário + pessoa), para a lojista saber o que fotografar/gravar.
- NUNCA sugira peças ou looks incompatíveis com o clima da estação atual ({estacao}).
- Use os diferenciais da loja para tornar a ideia irresistível.

Devolva APENAS este JSON, preenchendo TODOS os campos abaixo com conteúdo real:
{{
  "{campo_ideia}": "descrição específica e pronta de usar da ideia de {tipo}",
  "descricao_visual": "cena concreta: peça + ângulo + cenário + modelo/referência visual",
  "legenda": "legenda persuasiva usando PAS (se aplicável) + hashtags, 80-220 palavras...",
  "cta": "chamada para ação curta e específica",
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

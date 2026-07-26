"""
datas_comemorativas.py
Reconhece datas comemorativas relevantes para moda feminina no Brasil.
Datas móveis (Dia das Mães, Namorados etc.) são calculadas por regra simples;
para simplicidade e confiabilidade, mantemos uma tabela por ano com as principais.
"""
from datetime import date

# Datas fixas (mesma no ano todo)
DATAS_FIXAS = {
    (6, 12): "Dia dos Namorados",
    (12, 25): "Natal",
    (9, 23): "Início da Primavera",
    (12, 21): "Início do Verão",
    (3, 20): "Início do Outono",
    (6, 21): "Início do Inverno",
}

# Datas móveis conhecidas ano a ano (adicionar conforme necessário)
DATAS_MOVEIS = {
    2026: {
        (5, 10): "Dia das Mães",
        (11, 27): "Black Friday",
    },
    2027: {
        (5, 9): "Dia das Mães",
        (11, 26): "Black Friday",
    },
}

PERIODOS_LIQUIDACAO = [
    ((1, 2), (1, 31), "Liquidação de Verão"),
    ((7, 1), (7, 31), "Liquidação de Inverno"),
]


from typing import List

def estacao_do_ano(data: date) -> str:
    """Retorna a estação do ano no Hemisfério Sul (Brasil) para a data informada."""
    m, d = data.month, data.day
    if (m == 12 and d >= 21) or m in (1, 2) or (m == 3 and d <= 20):
        return "Verão"
    if (m == 3 and d >= 21) or m in (4, 5) or (m == 6 and d <= 20):
        return "Outono"
    if (m == 6 and d >= 21) or m in (7, 8) or (m == 9 and d <= 22):
        return "Inverno"
    return "Primavera"


def datas_proximas(data: date, dias_janela: int = 10) -> List[str]:
    """Retorna datas comemorativas dentro de uma janela de dias antes/depois da data (para dar
    contexto mesmo quando a data em si não é comemorativa, ex: 'Black Friday está chegando')."""
    from datetime import timedelta
    inicio = data - timedelta(days=dias_janela)
    fim = data + timedelta(days=dias_janela)
    return datas_da_semana(inicio, fim)


def datas_da_semana(data_inicio: date, data_fim: date) -> List[str]:
    """Retorna lista de nomes de datas comemorativas que caem dentro do intervalo da semana."""
    encontradas = []
    cursor = data_inicio
    from datetime import timedelta
    while cursor <= data_fim:
        chave = (cursor.month, cursor.day)
        if chave in DATAS_FIXAS:
            encontradas.append(DATAS_FIXAS[chave])
        moveis_ano = DATAS_MOVEIS.get(cursor.year, {})
        if chave in moveis_ano:
            encontradas.append(moveis_ano[chave])
        cursor += timedelta(days=1)

    for (m_ini, d_ini), (m_fim, d_fim), nome in PERIODOS_LIQUIDACAO:
        inicio_periodo = date(data_inicio.year, m_ini, d_ini)
        fim_periodo = date(data_inicio.year, m_fim, d_fim)
        if data_inicio <= fim_periodo and data_fim >= inicio_periodo:
            encontradas.append(nome)

    return list(dict.fromkeys(encontradas))  # remove duplicados mantendo ordem

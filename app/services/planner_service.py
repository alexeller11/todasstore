"""
planner_service.py
Cuida da estrutura de calendário (mês -> semana -> dia) e chama a IA
para gerar o planejamento semanal completo.
"""
import calendar
from datetime import date, timedelta

from app.extensions import db
from app.models import Mes, Semana, Dia, ChecklistItem, Loja, VersaoConteudo
from app.ai import ai_service, prompts
from app.services.checklist_service import criar_checklist_padrao
from app.services.datas_comemorativas import datas_da_semana, estacao_do_ano, datas_proximas

NOMES_MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

DIAS_SEMANA = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]


def obter_ou_criar_mes(ano, numero):
    mes = Mes.query.filter_by(ano=ano, numero=numero).first()
    if mes:
        return mes

    mes = Mes(ano=ano, numero=numero, nome=NOMES_MESES[numero])
    db.session.add(mes)
    db.session.flush()

    _gerar_semanas_e_dias(mes)
    db.session.commit()
    return mes


def _gerar_semanas_e_dias(mes):
    """Cria semanas (segunda a domingo) e os 7 dias de cada uma, cobrindo o mês inteiro."""
    primeiro_dia = date(mes.ano, mes.numero, 1)
    ultimo_dia_num = calendar.monthrange(mes.ano, mes.numero)[1]
    ultimo_dia = date(mes.ano, mes.numero, ultimo_dia_num)

    # volta até a segunda-feira que contém o primeiro dia do mês
    inicio_semana = primeiro_dia - timedelta(days=primeiro_dia.weekday())

    numero_semana = 1
    cursor = inicio_semana
    while cursor <= ultimo_dia:
        fim_semana = cursor + timedelta(days=6)
        semana = Semana(mes_id=mes.id, numero=numero_semana, data_inicio=cursor, data_fim=fim_semana)
        db.session.add(semana)
        db.session.flush()

        for i, nome_dia in enumerate(DIAS_SEMANA):
            data_dia = cursor + timedelta(days=i)
            dia = Dia(semana_id=semana.id, data=data_dia, dia_semana=nome_dia)
            db.session.add(dia)
            db.session.flush()
            criar_checklist_padrao(dia.id, salvar=False)

        numero_semana += 1
        cursor += timedelta(days=7)


def gerar_planejamento_semana(semana_id):
    """Chama a IA e preenche os 7 dias da semana com Stories + 3 Posts distribuídos."""
    semana = Semana.query.get_or_404(semana_id)
    loja = Loja.query.first()

    datas_especiais = datas_da_semana(semana.data_inicio, semana.data_fim)
    estacao = estacao_do_ano(semana.data_inicio)

    system_prompt, user_prompt = prompts.prompt_planejamento_semana(
        loja, semana.data_inicio.strftime("%d/%m/%Y"), datas_especiais, semana.promocao, estacao
    )
    resultado = ai_service.gerar_json(system_prompt, user_prompt)

    dias_gerados = resultado.get("dias", {})
    dias_por_nome = {d.dia_semana: d for d in semana.dias}

    for nome_dia, conteudo in dias_gerados.items():
        dia = dias_por_nome.get(nome_dia)
        if not dia:
            continue
        # Preserva a versão atual antes de sobrescrever (se houver conteúdo útil)
        _preservar_versao_se_existir(dia)
        dia.ideia_story = conteudo.get("ideia_story")
        dia.ideia_reels = conteudo.get("ideia_reels")
        dia.ideia_feed = conteudo.get("ideia_feed")
        dia.legenda = conteudo.get("legenda")
        dia.descricao_visual = conteudo.get("descricao_visual")
        dia.cta = conteudo.get("cta")
        dia.formato = conteudo.get("formato")
        dia.objetivo = conteudo.get("objetivo")
        dia.tempo_estimado = conteudo.get("tempo_estimado")
        dia.tem_post = bool(conteudo.get("tem_post"))

    db.session.commit()
    return semana


_CAMPO_POR_TIPO = {
    "story": "ideia_story",
    "reels": "ideia_reels",
    "feed": "ideia_feed",
}


def _preservar_versao_se_existir(dia, apenas_tipo=None):
    """Salva o conteúdo atual do dia em VersaoConteudo, se houver algo a preservar.
    Apenas_tipo opcional limita o snapshot a um tipo específico (story/reels/feed).
    Evita duplicar versões idênticas consecutivas."""
    for tipo, campo in _CAMPO_POR_TIPO.items():
        if apenas_tipo and tipo != apenas_tipo:
            continue
        conteudo = getattr(dia, campo)
        if not conteudo:
            continue
        ultima = (
            VersaoConteudo.query.filter_by(dia_id=dia.id, tipo=tipo)
            .order_by(VersaoConteudo.criado_em.desc())
            .first()
        )
        igual = ultima and ultima.conteudo == conteudo and ultima.legenda == (dia.legenda or "")
        if igual:
            continue
        versao = VersaoConteudo(
            dia_id=dia.id,
            tipo=tipo,
            conteudo=conteudo,
            descricao_visual=dia.descricao_visual,
            legenda=dia.legenda,
            cta=dia.cta,
            formato=dia.formato,
            objetivo=dia.objetivo,
            tempo_estimado=dia.tempo_estimado,
        )
        db.session.add(versao)


def gerar_nova_ideia_dia(dia_id, tipo):
    """Regenera a ideia de um único dia (botão "Gerar nova ideia")."""
    dia = Dia.query.get_or_404(dia_id)
    loja = Loja.query.first()

    estacao = estacao_do_ano(dia.data)
    datas_perto = datas_proximas(dia.data)
    promocao = dia.semana.promocao if dia.semana else None

    system_prompt, user_prompt = prompts.prompt_nova_ideia_dia(
        loja, dia.dia_semana, tipo,
        data=dia.data.strftime("%d/%m/%Y"), estacao=estacao, datas_proximas=datas_perto,
        promocao=promocao,
    )
    resultado = ai_service.gerar_json(system_prompt, user_prompt)

    campo_ideia = _CAMPO_POR_TIPO.get(tipo)
    conteudo_ideia = (resultado.get(campo_ideia) or "").strip() if campo_ideia else ""
    if not conteudo_ideia:
        raise RuntimeError(
            "A IA não retornou uma ideia válida dessa vez. Tente gerar novamente."
        )

    # Preserva a versão atual ANTES de sobrescrever (só do tipo que está sendo regenerado)
    _preservar_versao_se_existir(dia, apenas_tipo=tipo)

    if tipo == "story":
        dia.ideia_story = conteudo_ideia
    elif tipo == "reels":
        dia.ideia_reels = conteudo_ideia
        dia.tem_post = True
    elif tipo == "feed":
        dia.ideia_feed = conteudo_ideia
        dia.tem_post = True

    dia.legenda = resultado.get("legenda") or dia.legenda
    dia.descricao_visual = resultado.get("descricao_visual") or dia.descricao_visual
    dia.cta = resultado.get("cta") or dia.cta
    dia.formato = resultado.get("formato") or dia.formato
    dia.objetivo = resultado.get("objetivo") or dia.objetivo
    dia.tempo_estimado = resultado.get("tempo_estimado") or dia.tempo_estimado

    db.session.commit()
    return dia


def restaurar_versao(versao_id):
    """Copia uma VersaoConteudo de volta para o dia corrente.
    Antes de restaurar, preserva o conteúdo atual como nova versão (para o caso
    de a lojista querer voltar novamente)."""
    versao = VersaoConteudo.query.get_or_404(versao_id)
    dia = versao.dia
    tipo = versao.tipo

    _preservar_versao_se_existir(dia, apenas_tipo=tipo)

    campo = _CAMPO_POR_TIPO.get(tipo)
    if campo:
        setattr(dia, campo, versao.conteudo)
        if tipo in ("reels", "feed"):
            dia.tem_post = True

    dia.descricao_visual = versao.descricao_visual or dia.descricao_visual
    dia.legenda = versao.legenda or dia.legenda
    dia.cta = versao.cta or dia.cta
    dia.formato = versao.formato or dia.formato
    dia.objetivo = versao.objetivo or dia.objetivo
    dia.tempo_estimado = versao.tempo_estimado or dia.tempo_estimado

    db.session.commit()
    return versao

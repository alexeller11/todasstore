from datetime import date
from app.models import Dia, Semana, Mes


def progresso_mes(mes_id):
    mes = Mes.query.get_or_404(mes_id)
    dias = [d for semana in mes.semanas for d in semana.dias]
    total_dias = len(dias)
    stories_feitos = sum(1 for d in dias if d.story_feito)
    posts_feitos = sum(1 for d in dias if d.post_feito)
    dias_completos = sum(1 for d in dias if d.dia_completo)
    hoje = date.today()
    dias_atrasados = sum(1 for d in dias if d.data < hoje and not d.dia_completo)

    percentual = round((dias_completos / total_dias) * 100) if total_dias else 0

    return {
        "total_dias": total_dias,
        "stories_feitos": stories_feitos,
        "posts_feitos": posts_feitos,
        "dias_completos": dias_completos,
        "dias_atrasados": dias_atrasados,
        "percentual_conclusao": percentual,
    }


def progresso_semana(semana_id):
    semana = Semana.query.get_or_404(semana_id)
    dias = semana.dias
    total_dias = len(dias)
    stories_feitos = sum(1 for d in dias if d.story_feito)
    posts_feitos = sum(1 for d in dias if d.post_feito)
    dias_completos = sum(1 for d in dias if d.dia_completo)
    percentual = round((dias_completos / total_dias) * 100) if total_dias else 0

    return {
        "total_dias": total_dias,
        "stories_feitos": stories_feitos,
        "posts_feitos": posts_feitos,
        "dias_completos": dias_completos,
        "percentual_conclusao": percentual,
    }


def resumo_textual_semana(semana_id):
    """Gera um resumo simples em texto, usado como entrada para o prompt de insight semanal."""
    semana = Semana.query.get_or_404(semana_id)
    linhas = []
    for dia in semana.dias:
        partes = [f"{dia.dia_semana}:"]
        partes.append("story feito" if dia.story_feito else "sem story")
        if dia.tem_post:
            partes.append("post feito" if dia.post_feito else "post planejado mas não feito")
            if dia.objetivo:
                partes.append(f"objetivo: {dia.objetivo}")
        linhas.append(" - ".join(partes))
    return "\n".join(linhas)

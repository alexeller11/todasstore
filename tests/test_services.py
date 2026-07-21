import pytest
from datetime import date
from app.services.datas_comemorativas import estacao_do_ano, datas_da_semana

def test_estacao_do_ano():
    assert estacao_do_ano(date(2026, 1, 15)) == "Verão"
    assert estacao_do_ano(date(2026, 4, 15)) == "Outono"
    assert estacao_do_ano(date(2026, 7, 15)) == "Inverno"
    assert estacao_do_ano(date(2026, 10, 15)) == "Primavera"

def test_datas_da_semana_natal():
    datas = datas_da_semana(date(2026, 12, 20), date(2026, 12, 26))
    assert "Natal" in datas
    assert "Início do Verão" in datas

def test_datas_da_semana_black_friday():
    datas = datas_da_semana(date(2026, 11, 23), date(2026, 11, 29))
    assert "Black Friday" in datas

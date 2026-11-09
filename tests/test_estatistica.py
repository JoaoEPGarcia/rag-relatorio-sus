# -*- coding: utf-8 -*-
"""Testes das contas estatísticas da avaliação.

Wilson e McNemar são conferidos contra o statsmodels, que serve de oráculo
independente. O intervalo da diferença pareada (Newcombe, método 10) não
existe no statsmodels; é conferido pelas propriedades que ele precisa ter.
"""

import math

import pytest
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.proportion import proportion_confint

from rag_sus.avaliacao.estatistica import (
    diferenca_pareada,
    mcnemar_exato,
    tabela_pareada,
    wilson,
)


@pytest.mark.parametrize("acertos,n", [(48, 60), (30, 60), (1, 50), (59, 60), (7, 10)])
def test_wilson_bate_com_o_statsmodels(acertos, n):
    esperado = proportion_confint(acertos, n, alpha=0.05, method="wilson")

    r = wilson(acertos, n)

    assert r.proporcao == pytest.approx(acertos / n)
    assert (r.inferior, r.superior) == pytest.approx(esperado, abs=1e-12)


def test_wilson_nos_extremos_fica_dentro_de_zero_e_um():
    assert wilson(0, 60).inferior == pytest.approx(0.0, abs=1e-12)
    assert wilson(60, 60).superior == pytest.approx(1.0, abs=1e-12)
    assert wilson(0, 60).superior > 0


def test_wilson_recusa_n_zero_e_acertos_impossiveis():
    with pytest.raises(ValueError):
        wilson(0, 0)
    with pytest.raises(ValueError):
        wilson(61, 60)


@pytest.mark.parametrize("b,c", [(10, 2), (2, 10), (5, 5), (0, 7), (13, 0), (1, 1)])
def test_mcnemar_exato_bate_com_o_statsmodels(b, c):
    esperado = mcnemar([[20, b], [c, 15]], exact=True).pvalue

    assert mcnemar_exato(b, c) == pytest.approx(esperado, abs=1e-12)


def test_mcnemar_sem_pares_discordantes_da_um():
    assert mcnemar_exato(0, 0) == 1.0


def test_tabela_pareada_conta_os_quatro_casos():
    a_certo = [True, True, False, False, True]
    b_certo = [True, False, True, False, False]

    t = tabela_pareada(a_certo, b_certo)

    assert (t.ambos, t.so_a, t.so_b, t.nenhum) == (1, 2, 1, 1)


def test_tabela_pareada_recusa_listas_de_tamanhos_diferentes():
    with pytest.raises(ValueError):
        tabela_pareada([True], [True, False])


class TestDiferencaPareada:
    def test_estimativa_e_a_diferenca_das_proporcoes(self):
        r = diferenca_pareada(ambos=30, so_a=15, so_b=3, nenhum=12)

        assert r.diferenca == pytest.approx((15 - 3) / 60)

    def test_intervalo_contem_a_estimativa_e_fica_em_menos_um_a_um(self):
        for caso in [(30, 15, 3, 12), (0, 0, 0, 10), (10, 0, 0, 0), (5, 20, 0, 0), (0, 0, 20, 5)]:
            r = diferenca_pareada(*caso)
            assert -1.0 <= r.inferior <= r.diferenca <= r.superior <= 1.0

    def test_trocar_as_condicoes_espelha_o_intervalo(self):
        r = diferenca_pareada(30, 15, 3, 12)
        espelho = diferenca_pareada(30, 3, 15, 12)

        assert espelho.diferenca == pytest.approx(-r.diferenca)
        assert (espelho.inferior, espelho.superior) == pytest.approx((-r.superior, -r.inferior))

    def test_sem_discordancia_o_intervalo_e_simetrico_em_zero(self):
        r = diferenca_pareada(25, 6, 6, 23)

        assert r.diferenca == 0
        assert r.inferior == pytest.approx(-r.superior)

    def test_diferenca_grande_exclui_o_zero_e_pequena_nao(self):
        assert diferenca_pareada(20, 25, 2, 13).inferior > 0
        assert diferenca_pareada(25, 4, 3, 28).inferior < 0 < diferenca_pareada(25, 4, 3, 28).superior

    def test_intervalo_encolhe_com_mais_pares(self):
        pequeno = diferenca_pareada(10, 6, 2, 2)
        grande = diferenca_pareada(100, 60, 20, 20)

        assert (grande.superior - grande.inferior) < (pequeno.superior - pequeno.inferior)

    def test_valor_conferido_a_mao(self):
        # a=30, b=15, c=3, d=12, n=60. Wilson de 45/60 e de 33/60, phi pela
        # fórmula de Newcombe (1998), método 10. Conta refeita aqui, passo a passo.
        n, z = 60, 1.959963984540054

        def wil(x):
            p = x / n
            centro = (p + z * z / (2 * n)) / (1 + z * z / n)
            meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
            return p, centro - meia, centro + meia

        p1, l1, u1 = wil(45)
        p2, l2, u2 = wil(33)
        phi = (30 * 12 - 15 * 3) / math.sqrt(45 * 15 * 33 * 27)
        d = p1 - p2
        inf = d - math.sqrt((p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2)
        sup = d + math.sqrt((u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2)

        r = diferenca_pareada(30, 15, 3, 12)
        assert (r.inferior, r.superior) == pytest.approx((inf, sup), abs=1e-12)

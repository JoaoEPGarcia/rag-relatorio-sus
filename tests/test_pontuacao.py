# -*- coding: utf-8 -*-
"""Testes da pontuação das respostas e das Classes de erro."""

import pytest

from rag_sus.avaliacao.pontuacao import (
    acerto_citacao,
    acerto_numerico,
    acerto_recuperacao,
    classificar_erro,
    extrair_numeros,
)


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("as OSS atendem 32,9% mais pacientes", [32.9]),
        ("434.679 em 2025, contra 373.444 em 2023", [434679, 2025, 373444, 2023]),
        ("R$ 1.236 em 2023", [1236, 2023]),
        ("efeito de −0,62 p.p.", [-0.62]),
        ("efeito de -0,62 p.p.", [-0.62]),
        ("taxa de 0,0593", [0.0593]),
        ("entre 3,7% e 7,1%", [3.7, 7.1]),
        ("1.000.000 de reais", [1_000_000]),
        ("sem números aqui", []),
    ],
)
def test_extrair_numeros_no_formato_brasileiro(texto, esperado):
    assert extrair_numeros(texto) == pytest.approx(esperado)


def test_hifen_entre_palavra_e_numero_nao_e_sinal():
    assert extrair_numeros("faixa 4,72%–7,24%") == pytest.approx([4.72, 7.24])
    assert extrair_numeros("estrato E3-4") == pytest.approx([3, 4])


class TestAcertoNumerico:
    def test_todos_os_valores_esperados_presentes_e_acerto(self):
        assert acerto_numerico("Foram 434.679 cirurgias em 2025.", (434679,))

    def test_falta_um_valor_e_erro(self):
        assert not acerto_numerico("Pagou R$ 4,3 bilhões.", (4.3, 4.45))

    def test_numero_arredondado_e_erro(self):
        assert not acerto_numerico("A produção foi 45% maior.", (44.7,))

    def test_numero_escrito_com_ponto_decimal_ingles_e_erro(self):
        # O prompt manda copiar os números como estão no relatório.
        assert not acerto_numerico("As OSS atendem 32.9% mais.", (32.9,))


def test_acerto_citacao_basta_uma_pagina_do_gabarito():
    assert acerto_citacao(citadas=(70, 12), gabarito=(70,))
    assert not acerto_citacao(citadas=(71,), gabarito=(70,))
    assert not acerto_citacao(citadas=(), gabarito=(70,))


def test_acerto_recuperacao():
    assert acerto_recuperacao(recuperadas=(18, 63, 70), gabarito=(70, 71))
    assert not acerto_recuperacao(recuperadas=(18, 63), gabarito=(70,))


class TestClassesDeErro:
    def test_resposta_certa_com_citacao_certa_nao_e_erro(self):
        assert classificar_erro(True, False, True, True, respondivel=True) is None

    def test_abstencao_em_pergunta_respondivel(self):
        assert classificar_erro(False, True, False, False, respondivel=True) == "abstenção indevida"

    def test_resposta_errada_sem_a_pagina_recuperada(self):
        assert classificar_erro(False, False, False, False, respondivel=True) == "falha de recuperação"

    def test_resposta_errada_com_a_pagina_recuperada(self):
        assert classificar_erro(False, False, False, True, respondivel=True) == "falha de leitura"

    def test_condicao_sem_recuperacao_nao_tem_falha_de_recuperacao(self):
        assert classificar_erro(False, False, False, None, respondivel=True) == "falha de leitura"

    def test_resposta_certa_com_pagina_errada(self):
        assert classificar_erro(True, False, False, True, respondivel=True) == "citação errada"

    def test_pergunta_sem_resposta(self):
        assert classificar_erro(False, True, False, None, respondivel=False) is None
        assert classificar_erro(False, False, False, None, respondivel=False) == "resposta inventada"

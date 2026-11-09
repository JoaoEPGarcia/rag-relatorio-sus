# -*- coding: utf-8 -*-
"""Testes do Gabarito e da trava da Revisão.

A regra do projeto: nenhum Gabarito entra na avaliação sem a Revisão do
autor. Ela vale como código: o carregamento recusa o arquivo inteiro se
alguma linha estiver sem revisão.
"""

import pytest

from rag_sus.avaliacao.gabarito import (
    GabaritoInvalido,
    GabaritoNaoRevisado,
    carregar_gabarito,
)

CABECALHO = "id,pergunta,tipo,resposta,valores,paginas,revisado,observacao\n"


def escrever(tmp_path, linhas):
    caminho = tmp_path / "gabarito.csv"
    caminho.write_text(CABECALHO + "".join(l + "\n" for l in linhas), encoding="utf-8")
    return caminho


LINHA_OK = 'G01,"Quantos hospitais tem o painel?",numero_prosa,"275 hospitais",275,6,MF 2026-11-10,'
LINHA_SEM = 'G51,"Qual o orçamento do SUS em 1990?",sem_resposta,"O relatório não trata disso.",,,MF 2026-11-10,'


def test_carrega_linhas_revisadas(tmp_path):
    itens = carregar_gabarito(escrever(tmp_path, [LINHA_OK, LINHA_SEM]))

    assert [i.id for i in itens] == ["G01", "G51"]
    assert itens[0].paginas == (6,)
    assert itens[0].valores == (275.0,)
    assert itens[0].respondivel and not itens[1].respondivel


def test_linha_sem_revisao_trava_o_arquivo_inteiro(tmp_path):
    nao_revisada = LINHA_OK.replace("G01", "G02").replace("MF 2026-11-10", "")

    with pytest.raises(GabaritoNaoRevisado) as erro:
        carregar_gabarito(escrever(tmp_path, [LINHA_OK, nao_revisada]))

    assert "G02" in str(erro.value)


def test_revisao_so_com_espacos_nao_conta(tmp_path):
    em_branco = LINHA_OK.replace("MF 2026-11-10", "   ")

    with pytest.raises(GabaritoNaoRevisado):
        carregar_gabarito(escrever(tmp_path, [em_branco]))


def test_proposta_pode_ser_lida_sem_revisao_quando_pedido(tmp_path):
    # Para eu mostrar a proposta ao autor; a avaliação nunca usa este modo.
    nao_revisada = LINHA_OK.replace("MF 2026-11-10", "")

    itens = carregar_gabarito(escrever(tmp_path, [nao_revisada]), exigir_revisao=False)

    assert itens[0].revisado == ""


@pytest.mark.parametrize(
    "linha,trecho_da_mensagem",
    [
        (LINHA_OK.replace("numero_prosa", "chute"), "tipo"),
        (LINHA_OK.replace(",275,6,", ",275,,"), "página"),
        (LINHA_SEM.replace(",,,MF", ",,51,MF"), "sem resposta"),
        (LINHA_OK.replace(",275,6,", ",,6,"), "valores"),
        (LINHA_OK.replace("numero_prosa", "sintese"), "duas páginas"),
    ],
)
def test_linhas_incoerentes_sao_recusadas(tmp_path, linha, trecho_da_mensagem):
    with pytest.raises(GabaritoInvalido, match=trecho_da_mensagem):
        carregar_gabarito(escrever(tmp_path, [linha]))


def test_id_repetido_e_recusado(tmp_path):
    with pytest.raises(GabaritoInvalido, match="repetido"):
        carregar_gabarito(escrever(tmp_path, [LINHA_OK, LINHA_OK]))


def test_varias_paginas_e_valores_decimais_com_virgula(tmp_path):
    linha = 'G07,"Quanto pagou a Tabela?",sintese,"R$ 4,3 bi contra R$ 4,45 bi","4,3;4,45",63;69,MF,'

    item = carregar_gabarito(escrever(tmp_path, [linha]))[0]

    assert item.paginas == (63, 69)
    assert item.valores == (4.3, 4.45)

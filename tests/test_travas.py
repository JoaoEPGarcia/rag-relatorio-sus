# -*- coding: utf-8 -*-
"""Testes da trava de congelamento dos parâmetros (ADR 0002)."""

import pytest

from rag_sus.avaliacao.travas import ParametrosNaoCongelados, verificar_congelamento


def test_parametros_nao_congelados_travam_a_rodada_principal():
    with pytest.raises(ParametrosNaoCongelados, match="congelado"):
        verificar_congelamento(False, "")


def test_parametros_congelados_mas_nao_commitados_travam():
    with pytest.raises(ParametrosNaoCongelados, match="commit"):
        verificar_congelamento(True, " M parametros.toml\n")


def test_parametros_congelados_e_commitados_liberam():
    verificar_congelamento(True, "")

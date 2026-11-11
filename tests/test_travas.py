# -*- coding: utf-8 -*-
"""Testes das travas da Rodada: congelamento dos parâmetros (ADR 0002) e o execucao.json."""

import json

import pytest

from rag_sus.avaliacao.travas import (
    ParametrosMudaram,
    ParametrosNaoCongelados,
    ler_commits,
    registrar_execucao,
    verificar_congelamento,
)

PARAMETROS = {"k": 6, "modelo_respondedor": "gemini-3.8-flash", "reservas_juiz": ["b", "c"]}


def test_parametros_nao_congelados_travam_a_rodada_principal():
    with pytest.raises(ParametrosNaoCongelados, match="congelado"):
        verificar_congelamento(False, "")


def test_parametros_congelados_mas_nao_commitados_travam():
    with pytest.raises(ParametrosNaoCongelados, match="commit"):
        verificar_congelamento(True, " M parametros.toml\n")


def test_parametros_congelados_e_commitados_liberam():
    verificar_congelamento(True, "")


def ler(pasta):
    return json.loads((pasta / "execucao.json").read_text(encoding="utf-8"))


def test_retomar_a_rodada_guarda_os_commits_anteriores_na_ordem_e_sem_repetir(tmp_path):
    for commit in ("aaaaaaa", "bbbbbbb", "aaaaaaa", "ccccccc"):
        registrar_execucao(tmp_path, commit, PARAMETROS)

    dados = ler(tmp_path)
    assert dados["commits"] == ["aaaaaaa", "bbbbbbb", "ccccccc"]
    assert dados["parametros"] == PARAMETROS
    assert ler_commits(dados) == ["aaaaaaa", "bbbbbbb", "ccccccc"]


def test_execucao_json_antigo_com_um_commit_so_e_lido_como_lista_de_um(tmp_path):
    # o formato que scripts/03_rodar_avaliacao.py gravava antes, sobrescrito a cada retomada
    antigo = {"commit": "fc1a063", "parametros": PARAMETROS}
    (tmp_path / "execucao.json").write_text(json.dumps(antigo), encoding="utf-8")
    assert ler_commits(antigo) == ["fc1a063"]

    registrar_execucao(tmp_path, "ad0ad19", PARAMETROS)

    assert ler_commits(ler(tmp_path)) == ["fc1a063", "ad0ad19"]


def test_retomar_com_parametros_diferentes_dos_registrados_e_recusado(tmp_path):
    registrar_execucao(tmp_path, "aaaaaaa", PARAMETROS)
    antes = (tmp_path / "execucao.json").read_bytes()

    with pytest.raises(ParametrosMudaram, match="k"):
        registrar_execucao(tmp_path, "bbbbbbb", {**PARAMETROS, "k": 8})
    assert (tmp_path / "execucao.json").read_bytes() == antes


def test_parametros_em_tupla_valem_o_mesmo_que_em_lista_como_ficam_no_json(tmp_path):
    registrar_execucao(tmp_path, "aaaaaaa", PARAMETROS)
    registrar_execucao(tmp_path, "bbbbbbb", {**PARAMETROS, "reservas_juiz": ("b", "c")})
    assert ler_commits(ler(tmp_path)) == ["aaaaaaa", "bbbbbbb"]


def test_rodada_de_desenvolvimento_pode_mudar_os_parametros_e_grava_os_novos(tmp_path):
    registrar_execucao(tmp_path, "aaaaaaa", PARAMETROS, exigir_mesmos_parametros=False)
    registrar_execucao(tmp_path, "bbbbbbb", {**PARAMETROS, "k": 8}, exigir_mesmos_parametros=False)

    dados = ler(tmp_path)
    assert dados["parametros"]["k"] == 8 and dados["commits"] == ["aaaaaaa", "bbbbbbb"]

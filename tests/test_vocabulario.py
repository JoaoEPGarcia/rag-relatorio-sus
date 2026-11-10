# -*- coding: utf-8 -*-
"""O vocabulário que a análise e as figuras compartilham: nomes, desempate e leitura do IC."""

from pathlib import Path

from rag_sus import config
from rag_sus.avaliacao.vocabulario import (
    CLASSES_DAS_RESPONDIVEIS,
    CLASSES_DE_ERRO,
    chave_por_tipo,
    juntar,
    lado_do_ic,
    mais_frequentes,
    rotulo_condicao,
)


def test_rotulo_da_condicao_abre_com_maiuscula():
    assert rotulo_condicao("contexto_completo") == "Contexto completo"
    assert rotulo_condicao("com_rag") == "Com RAG"


def test_juntar_em_portugues_e_em_ingles():
    assert juntar(["a"]) == "a"
    assert juntar(["a", "b", "c"]) == "a, b e c"
    assert juntar(["a", "b"], "and") == "a and b"


def test_mais_frequentes_devolve_todas_as_empatadas_na_ordem_e_nenhuma_sem_erro():
    assert mais_frequentes({"x": 1, "y": 3, "z": 3}) == ("y", "z")
    assert mais_frequentes({"x": 0, "y": 0}) == ()


def test_lado_do_ic_acima_abaixo_ou_incluindo_o_zero():
    assert lado_do_ic(0.02, 0.3) == 1
    assert lado_do_ic(-0.3, -0.02) == -1
    assert lado_do_ic(-0.1, 0.1) == 0


def test_classes_das_respondiveis_deixam_de_fora_a_resposta_inventada():
    assert "resposta_inventada" in CLASSES_DE_ERRO
    assert "resposta_inventada" not in CLASSES_DAS_RESPONDIVEIS
    assert CLASSES_DE_ERRO["falha_leitura"].nome_en == "reading failure"
    assert chave_por_tipo("sintese", "falha_leitura") == "com_rag_tipo_sintese_falha_leitura"


def test_na_raiz_leva_um_caminho_de_config_para_outra_raiz(tmp_path):
    assert config.na_raiz(config.RODADAS, tmp_path) == tmp_path / "resultados" / "rodadas"
    assert config.na_raiz(config.TEX_DO_RELATORIO, Path("p")) == Path("p") / "relatorio" / "relatorio.tex"

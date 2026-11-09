# -*- coding: utf-8 -*-
"""Testes da análise dos resultados consolidados de uma Rodada."""

import pytest

from rag_sus.avaliacao.analise import comparar, concordancia, erros_por_tipo, resumir


def linha(id_, acerto, tipo="numero_prosa", respondivel=True, citacao=True, recuperacao=True,
          abstencao=False, classe=None, custo=0.01, latencia=2.0, fallback=False, juiz=None, regra=None):
    return {
        "id": id_, "tipo": tipo, "respondivel": respondivel, "acerto_resposta": acerto,
        "acerto_citacao": citacao if respondivel else None,
        "acerto_recuperacao": recuperacao if respondivel else None,
        "abstencao": abstencao, "classe_erro": classe, "custo_usd": custo, "custo_juiz_usd": 0.0,
        "latencia_s": latencia, "usou_fallback": fallback, "veredicto_juiz": juiz,
        "acerto_regra": acerto if regra is None else regra,
    }


def test_resumo_separa_respondiveis_das_sem_resposta():
    linhas = [linha("G1", True), linha("G2", False, classe="falha de leitura"),
              linha("G3", True, citacao=False, classe="citação errada"),
              linha("S1", True, tipo="sem_resposta", respondivel=False, abstencao=True),
              linha("S2", False, tipo="sem_resposta", respondivel=False, classe="resposta inventada")]

    r = resumir(linhas)

    assert r["n_respondiveis"] == 3 and r["n_sem_resposta"] == 2
    assert r["acerto_resposta"].proporcao == pytest.approx(2 / 3)
    assert r["acerto_citacao"].proporcao == pytest.approx(2 / 3)
    assert r["abstencao_correta"].proporcao == pytest.approx(1 / 2)
    assert r["erros"] == {"falha de leitura": 1, "citação errada": 1, "resposta inventada": 1}


def test_resumo_sem_recuperacao_quando_a_condicao_nao_recupera():
    r = resumir([linha("G1", True, recuperacao=None)])
    assert r["acerto_recuperacao"] is None


def test_resumo_custo_e_latencia():
    r = resumir([linha("G1", True, custo=0.02, latencia=1.0), linha("G2", True, custo=0.04, latencia=3.0),
                 linha("G3", True, custo=0.03, latencia=10.0)])
    assert r["custo_medio_usd"] == pytest.approx(0.03)
    assert r["latencia_mediana_s"] == pytest.approx(3.0)
    assert r["n_fallback"] == 0


def test_comparar_pareia_pelo_id_e_ignora_sem_resposta():
    a = [linha("G1", True), linha("G2", True), linha("G3", False),
         linha("S1", True, tipo="sem_resposta", respondivel=False)]
    b = [linha("G3", False), linha("G2", False), linha("G1", True),
         linha("S1", False, tipo="sem_resposta", respondivel=False)]

    c = comparar(a, b)

    t = c["tabela"]
    assert (t.ambos, t.so_a, t.so_b, t.nenhum) == (1, 1, 0, 1)
    assert c["diferenca"].diferenca == pytest.approx(1 / 3)
    assert c["p_mcnemar"] == pytest.approx(1.0)


def test_comparar_recusa_conjuntos_diferentes_de_perguntas():
    with pytest.raises(ValueError):
        comparar([linha("G1", True)], [linha("G2", True)])


def test_erros_por_tipo_conta_so_respondiveis_com_erro():
    linhas = [linha("G1", False, tipo="numero_tabela", classe="falha de leitura"),
              linha("G2", False, tipo="numero_tabela", classe="falha de recuperação"),
              linha("G3", True, tipo="conceito"),
              linha("G4", False, tipo="conceito", classe="falha de leitura")]

    t = erros_por_tipo(linhas)

    assert t["numero_tabela"] == {"falha de leitura": 1, "falha de recuperação": 1, "n": 2}
    assert t["conceito"] == {"falha de leitura": 1, "n": 2}


def test_concordancia_entre_rodadas_usa_o_veredicto_sem_revisao():
    principal = [linha("G1", True, regra=True), linha("G2", False, juiz=False, regra=None),
                 linha("G3", True, regra=True)]
    repeticao = [linha("G1", True, regra=True), linha("G2", True, juiz=True, regra=None),
                 linha("G3", True, regra=True)]

    assert concordancia(principal, repeticao) == pytest.approx(2 / 3)

# -*- coding: utf-8 -*-
"""Testes da seam "da Rodada aos números": Rodadas sintéticas -> registro e tabelas.

As Rodadas e a folha de Revisão são gravadas numa pasta temporária, nunca em
resultados/. As contas esperadas saem de fora do código testado: o
statsmodels para Wilson e McNemar, e contagens escritas à mão.
"""

import csv
import json

import pytest
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.proportion import proportion_confint

from rag_sus import numeros
from rag_sus.avaliacao.resultados import analisar
from rag_sus.avaliacao.rodada import RevisaoIncompleta

TIPOS = ("numero_prosa", "numero_tabela", "numero_legenda", "conceito", "sintese")
RESPONDIVEIS = [f"G{i:02d}" for i in range(1, 51)]  # 10 de cada Tipo, na ordem de TIPOS
SEM_RESPOSTA = [f"S{i:02d}" for i in range(1, 11)]


def tipo_de(id_):
    return "sem_resposta" if id_.startswith("S") else TIPOS[(int(id_[1:]) - 1) // 10]


def linha(id_, condicao, acerto, *, juiz=None, citacao=None, recuperacao=True, abstencao=None,
          tokens=1000, latencia=2.0, fallback=False):
    """Uma linha de Rodada no formato de rodada._responder_e_pontuar.

    `juiz` None: o Veredicto saiu da regra. True/False: o Juiz julgou (e a regra não bastou).
    """
    respondivel = not id_.startswith("S")
    if abstencao is None:
        abstencao = (not respondivel and acerto)
    return {
        "id": id_, "tipo": tipo_de(id_), "respondivel": respondivel, "condicao": condicao,
        "pergunta": f"Qual é o valor pedido em {id_}?", "gabarito": f"Gabarito de {id_}.",
        "paginas_gabarito": [70] if respondivel else [],
        "resposta": f"Resposta de {id_}.", "paginas_citadas": [70], "abstencao": abstencao,
        "paginas_recuperadas": [70], "trechos_recuperados": [],
        "acerto_regra": (acerto if juiz is None else None) if respondivel else acerto,
        "veredicto_juiz": juiz, "justificativa_juiz": "",
        "acerto_citacao": (acerto if citacao is None else citacao) if respondivel else None,
        "acerto_recuperacao": recuperacao if (respondivel and condicao == "com_rag") else None,
        "modelo_que_respondeu": "gemini-3.8-flash", "usou_fallback": fallback,
        "tokens_entrada": tokens, "tokens_saida": 50, "tokens_cache_escrita": 0, "tokens_cache_leitura": 0,
        "custo_usd": 0.0, "custo_juiz_usd": 0.0, "latencia_s": latencia, "id_requisicao": "",
    }


def gravar_rodada(pasta, rodada, condicao, linhas):
    destino = pasta / rodada / f"{condicao}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        for l in linhas:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")


def gravar_folha(caminho, revisoes):
    """revisoes: lista de (condicao, id, veredicto_juiz, veredicto_revisado)."""
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["condicao", "id", "pergunta", "gabarito", "resposta", "veredicto_juiz",
                    "justificativa_juiz", "veredicto_revisado", "comentario"])
        for condicao, id_, juiz, revisado in revisoes:
            w.writerow([condicao, id_, "p", "g", "r", juiz, "j", revisado, ""])


def condicao_simples(condicao, acertos_respondiveis, abstencoes_corretas=10, **kw):
    """As `acertos_respondiveis` primeiras respondíveis acertam, pela regra; o resto erra."""
    linhas = [linha(i, condicao, n < acertos_respondiveis, **kw) for n, i in enumerate(RESPONDIVEIS)]
    linhas += [linha(i, condicao, n < abstencoes_corretas, **kw) for n, i in enumerate(SEM_RESPOSTA)]
    return linhas


@pytest.fixture
def projeto(tmp_path):
    """Pasta das Rodadas com a Rodada principal: com RAG 40/50, sem RAG 15/50, contexto completo 42/50."""
    rodadas = tmp_path / "rodadas"
    gravar_rodada(rodadas, "principal", "com_rag", condicao_simples("com_rag", 40, abstencoes_corretas=9))
    gravar_rodada(rodadas, "principal", "sem_rag", condicao_simples("sem_rag", 15))
    gravar_rodada(rodadas, "principal", "contexto_completo", condicao_simples("contexto_completo", 42))
    folha = tmp_path / "revisao_veredictos.csv"
    gravar_folha(folha, [])
    return {
        "rodadas": rodadas, "folha": folha,
        "numeros": tmp_path / "resultados" / "numeros.json", "tabelas": tmp_path / "relatorio" / "tabelas",
    }


def rodar(p):
    analisar(p["rodadas"], p["folha"], numeros_json=p["numeros"], pasta_tabelas=p["tabelas"])
    return numeros.carregar(p["numeros"])


def test_acerto_da_resposta_por_condicao_bate_com_wilson_independente(projeto):
    r = rodar(projeto)

    for condicao, acertos in (("com_rag", 40), ("sem_rag", 15), ("contexto_completo", 42)):
        inf, sup = proportion_confint(acertos, 50, alpha=0.05, method="wilson")
        assert r[f"{condicao}_n_respondiveis"]["valor"] == 50
        assert r[f"{condicao}_acertos_resposta"]["valor"] == acertos
        assert r[f"{condicao}_acerto_resposta"]["valor"] == pytest.approx(acertos / 50)
        assert r[f"{condicao}_acerto_resposta_inf"]["valor"] == pytest.approx(inf, abs=1e-6)
        assert r[f"{condicao}_acerto_resposta_sup"]["valor"] == pytest.approx(sup, abs=1e-6)
    assert r["com_rag_acerto_resposta"]["texto"] == "80,0%"


def com_juiz(p, condicao, juizes):
    """Regrava a Rodada principal da Condição com Veredictos do Juiz nas Perguntas de `juizes` (id -> acerto)."""
    caminho = p["rodadas"] / "principal" / f"{condicao}.jsonl"
    linhas = [json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines()]
    for l in linhas:
        if l["id"] in juizes:
            l["acerto_regra"], l["veredicto_juiz"] = None, juizes[l["id"]]
    gravar_rodada(p["rodadas"], "principal", condicao, linhas)


@pytest.mark.parametrize("comparacao,outra,tabela", [
    # com RAG acerta G01..G40; sem RAG, G01..G15; contexto completo, G01..G42
    ("com_rag_x_sem_rag", "sem_rag", (15, 25, 0, 10)),
    ("com_rag_x_contexto_completo", "contexto_completo", (40, 0, 2, 8)),
])
def test_comparacao_pareada_nas_respondiveis(projeto, comparacao, outra, tabela):
    r = rodar(projeto)

    ambos, so_com, so_outra, nenhum = tabela
    assert r[f"{comparacao}_n_pares"]["valor"] == 50
    assert r[f"{comparacao}_ambos"]["valor"] == ambos
    assert r[f"{comparacao}_so_com_rag"]["valor"] == so_com
    assert r[f"{comparacao}_so_{outra}"]["valor"] == so_outra
    assert r[f"{comparacao}_nenhum"]["valor"] == nenhum
    p = mcnemar([[ambos, so_com], [so_outra, nenhum]], exact=True).pvalue
    assert r[f"{comparacao}_p_mcnemar"]["valor"] == pytest.approx(p)
    d = (so_com - so_outra) / 50
    assert r[f"{comparacao}_diferenca"]["valor"] == pytest.approx(d)
    assert r[f"{comparacao}_diferenca_inf"]["valor"] < d < r[f"{comparacao}_diferenca_sup"]["valor"]


def test_comparacao_escreve_a_diferenca_em_pontos_percentuais_com_o_sinal_de_menos(projeto):
    r = rodar(projeto)
    assert r["com_rag_x_sem_rag_diferenca"]["texto"] == "50,0 p.p."
    assert r["com_rag_x_contexto_completo_diferenca"]["texto"] == "−4,0 p.p."
    assert r["com_rag_x_sem_rag_p_mcnemar"]["texto"] == "< 0,001"


def test_falta_de_revisao_trava_a_analise_e_lista_as_perguntas_pendentes(projeto):
    com_juiz(projeto, "com_rag", {"G41": True, "G42": False})
    com_juiz(projeto, "sem_rag", {"G43": False})
    gravar_folha(projeto["folha"], [("com_rag", "G41", "certo", "certo"), ("com_rag", "G42", "errado", ""),
                                    ("sem_rag", "G43", "errado", "")])

    with pytest.raises(RevisaoIncompleta) as erro:
        rodar(projeto)

    mensagem = str(erro.value)
    assert "com_rag: G42" in mensagem and "sem_rag: G43" in mensagem and "G41" not in mensagem
    assert not projeto["numeros"].exists()


def test_revisao_do_autor_vence_o_juiz_e_o_registro_conta_as_mudancas(projeto):
    # G41..G43 erraram pela regra na fixture (só as 40 primeiras acertam); o Juiz diz certo nas três
    com_juiz(projeto, "com_rag", {"G41": True, "G42": True, "G43": True})
    com_juiz(projeto, "sem_rag", {"G41": False})
    gravar_folha(projeto["folha"], [("com_rag", "G41", "certo", "certo"), ("com_rag", "G42", "certo", "errado"),
                                    ("com_rag", "G43", "certo", "errado"), ("sem_rag", "G41", "errado", "errado")])

    r = rodar(projeto)

    assert r["com_rag_acertos_resposta"]["valor"] == 41  # 40 da regra + G41; G42 e G43 o autor derrubou
    assert r["revisao_veredictos_juiz"]["valor"] == 4
    assert r["revisao_veredictos_revisados"]["valor"] == 4
    assert r["revisao_veredictos_mudados"]["valor"] == 2


def test_destaque_usa_so_as_respondiveis_e_as_sem_resposta_saem_a_parte(projeto):
    r = rodar(projeto)

    # sobre as 60, com RAG daria (40 + 9) / 60; o destaque é 40 / 50
    inf, sup = proportion_confint(40, 50, alpha=0.05, method="wilson")
    assert r["destaque_n_respondiveis"]["valor"] == 50
    assert r["destaque_acerto_com_rag"]["valor"] == pytest.approx(0.8)
    assert r["destaque_acerto_com_rag_inf"]["valor"] == pytest.approx(inf, abs=1e-6)
    assert r["destaque_acerto_com_rag_sup"]["valor"] == pytest.approx(sup, abs=1e-6)
    assert r["destaque_acerto_sem_rag"]["valor"] == pytest.approx(0.3)

    inf, sup = proportion_confint(9, 10, alpha=0.05, method="wilson")
    assert r["com_rag_n_sem_resposta"]["valor"] == 10
    assert r["com_rag_abstencoes_corretas"]["valor"] == 9
    assert r["com_rag_abstencao_correta"]["valor"] == pytest.approx(0.9)
    assert r["com_rag_abstencao_correta_inf"]["valor"] == pytest.approx(inf, abs=1e-6)
    assert r["com_rag_abstencao_correta_sup"]["valor"] == pytest.approx(sup, abs=1e-6)

# -*- coding: utf-8 -*-
"""Testes da folha de Revisão dos Veredictos em PDF (gerada da folha CSV, sem número digitado)."""

import csv

from rag_sus.avaliacao.folha_dos_veredictos import gerar_tex
from rag_sus.avaliacao.rodada import COLUNAS_FOLHA
from tests.test_folha_do_gabarito import relatorio_solto

COLUNAS_GABARITO = ["id", "pergunta", "tipo", "resposta", "valores", "paginas", "revisado", "observacao"]


def gravar(caminho, colunas, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas, lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)


def veredicto(condicao, id_, juiz, resposta="Resposta com 50% e R$ 3."):
    return {"condicao": condicao, "id": id_, "pergunta": f"Pergunta {id_}?", "gabarito": f"Gabarito {id_}.",
            "resposta": resposta, "veredicto_juiz": juiz, "justificativa_juiz": "Diz o mesmo.",
            "veredicto_revisado": "", "comentario": ""}


def test_folha_traz_cada_veredicto_por_condicao_com_as_contagens_do_script(tmp_path):
    folha, gabarito = tmp_path / "revisao_veredictos.csv", tmp_path / "gabarito.csv"
    gravar(folha, COLUNAS_FOLHA, [
        veredicto("com_rag", "G02", "certo"),
        veredicto("com_rag", "G03", "errado"),
        veredicto("contexto_completo", "G02", "certo"),
    ])
    gravar(gabarito, COLUNAS_GABARITO, [
        {"id": i, "pergunta": "", "tipo": "conceito", "resposta": "", "valores": "", "paginas": "4",
         "revisado": "JEPG", "observacao": ""} for i in ("G02", "G03")
    ])

    tex = gerar_tex(folha, gabarito)

    assert tex.count(r"\cartao{G02}") == 2 and tex.count(r"\cartao{G03}") == 1
    assert r"\section*{Com RAG}" in tex and r"\section*{Contexto completo}" in tex
    assert r"\section*{Sem RAG}" not in tex  # sem Veredicto do Juiz, sem seção
    assert r"\newcommand{\NumVeredictos}{3}" in tex
    assert r"\newcommand{\NumJuizCerto}{2}" in tex and r"\newcommand{\NumJuizErrado}{1}" in tex
    assert r"50\% e R\$ 3." in tex
    assert "Conceito ou método" in tex
    assert relatorio_solto(tex) == []  # Relatório-fonte, como o glossário pede

# -*- coding: utf-8 -*-
"""Testes da folha de Revisão do Gabarito em PDF (gerada do CSV, sem número digitado)."""

import csv

from rag_sus.avaliacao.folha_do_gabarito import escapar, gerar_tex

COLUNAS = ["id", "pergunta", "tipo", "resposta", "valores", "paginas", "revisado", "observacao"]


def gravar(caminho, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        for l in linhas:
            w.writerow(l)


def linha(id_, tipo="numero_prosa", observacao="", paginas="25", valores="6,13"):
    return {"id": id_, "pergunta": f"Pergunta {id_}?", "tipo": tipo, "resposta": "R$ 908 e 50% (η2)",
            "valores": valores, "paginas": paginas, "revisado": "", "observacao": observacao}


def test_escapa_o_que_o_pdflatex_nao_aceita():
    assert escapar("50% & R$ 3_1 #2 {x} a|b −0,62 η2 = 0,43") == (
        r"50\% \& R\$ 3\_1 \#2 \{x\} a\textbar{}b $-$0,62 $\eta$2 = 0,43")


def test_folha_traz_cada_pergunta_com_pagina_do_arquivo_e_os_alertas_no_roteiro(tmp_path):
    csv_ = tmp_path / "gabarito.csv"
    gravar(csv_, [
        linha("G01", observacao="p. 25: 'trecho' | CONFERIR: os mesmos valores aparecem também na p. 151"),
        linha("G43", tipo="conceito", valores="", paginas="150",
              observacao="p. 150: 'x' | ATENÇÃO: inconsistência. Considere trocar a pergunta."),
        linha("S01", tipo="sem_resposta", valores="", paginas="", observacao="Confirme a ausência."),
    ])

    tex = gerar_tex(csv_, tmp_path / "fonte.pdf")

    for id_ in ("G01", "G43", "S01"):
        assert f"{{{id_}}}" in tex
    # página impressa 25 = página 26 do arquivo (ADR 0004), com link para o PDF
    assert "p.~25" in tex and "page=26" in tex
    # o roteiro de prioridade lista os alertas e a candidata a troca, contados pelo script
    assert r"\newcommand{\NumPerguntas}{3}" in tex
    assert r"\newcommand{\NumAtencao}{1}" in tex and r"\newcommand{\NumConferir}{1}" in tex
    assert "Considere trocar" in tex
    assert r"\begin{document}" in tex and r"\end{document}" in tex


def test_barra_dentro_de_citacao_de_tabela_nao_abre_item_novo(tmp_path):
    csv_ = tmp_path / "gabarito.csv"
    gravar(csv_, [linha("G47", observacao="p. 162: 'Taxa | +9,9% | 0,0944' | p. 163: 'outra' | ATENÇÃO: veja")])

    tex = gerar_tex(csv_, tmp_path / "fonte.pdf")

    cartao = tex[tex.index(r"\cartao{G47}"):]
    assert cartao.count(r"  \item ") == 3
    assert r"Taxa \textbar{} +9,9\% \textbar{} 0,0944" in tex

# -*- coding: utf-8 -*-
"""Testes da folha de Revisão do Gabarito em PDF (gerada do CSV, sem número digitado)."""

import csv
import os
import re
import subprocess
import sys

from rag_sus.avaliacao.folha_do_gabarito import gerar_tex
from rag_sus.avaliacao.folha_do_kit import escapar

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


def relatorio_solto(tex):
    """Cada "relatório" sem dizer qual (o glossário pede Relatório-fonte ou Relatório de avaliação).

    O nome do documento, "relatório Gestão Hospitalar no SUS-SP", diz qual é.
    """
    return re.findall(r"(?i)\brelatório\b(?!-fonte| de avaliação| Gestão Hospitalar)", tex)


def test_folha_diz_relatorio_fonte_e_nunca_relatorio_solto(tmp_path):
    csv_ = tmp_path / "gabarito.csv"
    gravar(csv_, [linha("G01"), linha("S01", tipo="sem_resposta", valores="", paginas="")])

    assert relatorio_solto(gerar_tex(csv_, tmp_path / "fonte.pdf")) == []


def test_kit_vem_do_projeto_mesmo_sobre_uma_raiz_temporaria(tmp_path):
    # o kit é código, como o README.base.md: sob RAG_SUS_RAIZ, a raiz não tem estilo/
    csv_ = tmp_path / "gabarito.csv"
    gravar(csv_, [linha("G01")])
    codigo = ("import sys; from pathlib import Path; from rag_sus.avaliacao.folha_do_gabarito import gerar_tex; "
              "print(r'\\begin{document}' in gerar_tex(Path(sys.argv[1]), Path(sys.argv[2])))")
    r = subprocess.run([sys.executable, "-c", codigo, str(csv_), str(tmp_path / "fonte.pdf")],
                       env={**os.environ, "RAG_SUS_RAIZ": str(tmp_path / "raiz")}, capture_output=True, text=True)

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "True"


def test_barra_dentro_de_citacao_de_tabela_nao_abre_item_novo(tmp_path):
    csv_ = tmp_path / "gabarito.csv"
    gravar(csv_, [linha("G47", observacao="p. 162: 'Taxa | +9,9% | 0,0944' | p. 163: 'outra' | ATENÇÃO: veja")])

    tex = gerar_tex(csv_, tmp_path / "fonte.pdf")

    cartao = tex[tex.index(r"\cartao{G47}"):]
    assert cartao.count(r"  \item ") == 3
    assert r"Taxa \textbar{} +9,9\% \textbar{} 0,0944" in tex

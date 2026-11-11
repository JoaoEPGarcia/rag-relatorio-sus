# -*- coding: utf-8 -*-
"""Gera a folha de Revisão do Gabarito em PDF (ticket 08).

POR QUE ISTO EXISTE. O autor confere o Gabarito no PDF do Relatório-fonte;
esta folha põe cada Pergunta, a resposta proposta, os valores, as páginas
(com link para a página do arquivo) e os alertas da extração lado a lado. Ele
responde no chat só as exceções, e o agente preenche a coluna `revisado`.

A folha é de trabalho e fica fora do git: os links apontam para o caminho do
PDF nesta máquina. Regere depois de cada mudança no Gabarito.

Uso: uv run python scripts/gerar_folha_do_gabarito.py
"""

import sys

from rag_sus import config
from rag_sus.avaliacao.folha_do_gabarito import gerar_tex
from rag_sus.pipeline import compilar_pdf

PASTA = config.AVALIACAO / "revisao_gabarito"
NOME = "revisao_gabarito"


def main() -> int:
    PASTA.mkdir(parents=True, exist_ok=True)
    tex = PASTA / f"{NOME}.tex"
    tex.write_text(gerar_tex(config.GABARITO, config.PDF), encoding="utf-8", newline="\n")
    return 1 if compilar_pdf(tex, PASTA, "Folha de Revisão do Gabarito") else 0


if __name__ == "__main__":
    sys.exit(main())

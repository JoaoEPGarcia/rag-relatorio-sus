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

import subprocess
import sys

from rag_sus import config
from rag_sus.avaliacao.folha_do_gabarito import gerar_tex

PASTA = config.RAIZ / "avaliacao" / "revisao_gabarito"
NOME = "revisao_gabarito"


def main() -> int:
    PASTA.mkdir(parents=True, exist_ok=True)
    tex = PASTA / f"{NOME}.tex"
    tex.write_text(gerar_tex(config.GABARITO, config.RAIZ / "dados" / "relatorio_fonte.pdf"),
                   encoding="utf-8", newline="\n")
    for passada in (1, 2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                           cwd=PASTA, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print("\n".join(r.stdout.splitlines()[-30:]))
            print(f"pdflatex falhou na passada {passada}; o log está em {PASTA / (NOME + '.log')}")
            return 1
    print(f"Folha de Revisão do Gabarito: {PASTA / (NOME + '.pdf')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

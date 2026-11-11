# -*- coding: utf-8 -*-
"""Conferência do PDF do Relatório de avaliação, depois da compilação.

POR QUE ISTO EXISTE. Tabela que vaza a margem e linha que estoura não
aparecem no código: só no PDF. Este script falha (código 1) se algum texto do
PDF passa da medida larga do kit (papel menos 1 cm de cada lado) ou se o .log
tem Overfull \\hbox acima de 1 pt. Ver rag_sus.conferencia_pdf.

Uso: uv run python scripts/conferir_pdf.py
"""

import sys

from rag_sus import config
from rag_sus.conferencia_pdf import fora_da_margem, overfull

PDF = config.RELATORIO / "relatorio.pdf"
LOG = config.RELATORIO / "relatorio.log"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not PDF.exists():
        print(f"{PDF} não existe: compile o Relatório de avaliação antes.")
        return 1
    falhas = [f"página {p}: texto além da margem de 1 cm: «{t}»" for p, t in fora_da_margem(PDF)]
    if LOG.exists():
        falhas += [f"Overfull \\hbox de {o}" for o in overfull(LOG.read_text(encoding="utf-8", errors="replace"))]
    for f in falhas:
        print(f"FALHA: {f}")
    print("Conferência do PDF: " + ("ok" if not falhas else f"{len(falhas)} falha(s)"))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())

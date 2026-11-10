# -*- coding: utf-8 -*-
"""Gera a folha de Revisão dos Veredictos do Juiz em PDF (ticket 10).

POR QUE ISTO EXISTE. O autor revisa cada Veredicto do Juiz da Rodada
principal; esta folha mostra, por Condição, o Gabarito, a resposta e o
Veredicto com a justificativa. Ele responde no chat só onde discorda, e o
agente preenche `veredicto_revisado` em avaliacao/revisao_veredictos.csv.

A folha é de trabalho e fica fora do git. Regere depois de cada Rodada.

Uso: uv run python scripts/gerar_folha_dos_veredictos.py
"""

import subprocess
import sys

from rag_sus import config
from rag_sus.avaliacao.folha_dos_veredictos import gerar_tex

PASTA = config.RAIZ / "avaliacao" / "revisao_veredictos"
NOME = "revisao_veredictos"


def main() -> int:
    if not config.REVISAO_VEREDICTOS.exists():
        print(f"{config.REVISAO_VEREDICTOS} ainda não existe: ela sai ao fim da Rodada principal.")
        return 1
    PASTA.mkdir(parents=True, exist_ok=True)
    tex = PASTA / f"{NOME}.tex"
    tex.write_text(gerar_tex(config.REVISAO_VEREDICTOS, config.GABARITO), encoding="utf-8", newline="\n")
    for passada in (1, 2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                           cwd=PASTA, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print("\n".join(r.stdout.splitlines()[-30:]))
            print(f"pdflatex falhou na passada {passada}; o log está em {PASTA / (NOME + '.log')}")
            return 1
    print(f"Folha de Revisão dos Veredictos: {PASTA / (NOME + '.pdf')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

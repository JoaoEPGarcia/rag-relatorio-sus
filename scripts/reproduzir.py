# -*- coding: utf-8 -*-
"""Pipeline completo: refaz tudo a partir das Rodadas versionadas, sem chamar o modelo.

POR QUE ISTO EXISTE. Quem clona o repositório confere o resultado com um
comando. Os passos, nesta ordem, param no primeiro erro com o nome do passo:
  1. extração e índice (scripts/01_extrair.py, 02_indexar.py), só se faltarem;
  2. análise (04_analisar.py), que para se faltar a Rodada principal ou a Revisão;
  3. figuras (05_figuras.py; precisa de `uv sync --all-groups`);
  4. documentos (06_gerar_documentos.py): macros, NUMEROS_CANONICOS.md e README;
  5. compilação do Relatório de avaliação (pdflatex, duas ou três passadas);
  6. conferidor de números (conferir_numeros.py);
  7. conferência mecânica do Gabarito (conferir_gabarito.py).
A Rodada paga (03_rodar_avaliacao.py) nunca roda por aqui.

O .tex do Relatório de avaliação é o do projeto; o pdflatex roda na pasta
relatorio/ da raiz, de onde lê numeros.tex, tabelas/ e ../figuras/, e onde
grava o PDF. Sobre as Rodadas sintéticas (raiz temporária), a extração, o
índice e a conferência do Gabarito são pulados: a raiz não tem o PDF real.

Uso:
  uv run python scripts/reproduzir.py
Sobre as Rodadas sintéticas (Git Bash):
  export RAG_SUS_RAIZ="$(mktemp -d)"
  uv run python scripts/gerar_rodadas_sinteticas.py
  uv run python scripts/reproduzir.py
"""

import os
import subprocess
import sys

from rag_sus import config
from rag_sus.pipeline import compilar_relatorio, passos_do_pipeline, rodar

TEX = config.PROJETO / "relatorio" / "relatorio.tex"


def rodar_script(nome: str) -> int:
    """Roda scripts/<nome> com o mesmo Python, a mesma raiz e a saída em UTF-8 (Windows)."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(config.PROJETO / "scripts" / nome)], env=env).returncode


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Raiz: {config.RAIZ}", flush=True)
    passos = passos_do_pipeline(config.RAIZ, rodar_script, lambda: compilar_relatorio(TEX, config.RELATORIO))
    return rodar(passos)


if __name__ == "__main__":
    sys.exit(main())

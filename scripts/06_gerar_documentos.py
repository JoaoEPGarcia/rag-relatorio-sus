# -*- coding: utf-8 -*-
"""Passo 6: gera relatorio/numeros.tex, NUMEROS_CANONICOS.md e README.md.

POR QUE ISTO EXISTE. Nenhum número impresso é digitado (ADR 0003). Este passo
lê o registro resultados/numeros.json, que cada script alimenta, e escreve as
três saídas. Para mudar o texto do README, edite README.base.md, e não o
README.md.

O README.base.md e os .tex escritos à mão vêm sempre do projeto (são código,
como os scripts); o registro e as saídas, da raiz (RAG_SUS_RAIZ, se
definida). Assim o README pode ser gerado sobre as Rodadas sintéticas numa
raiz temporária. Se algum
marcador do README.base.md não tiver valor no registro, nada é escrito.

Uso: uv run python scripts/06_gerar_documentos.py
"""

import sys

from rag_sus import config, numeros
from rag_sus.documentos import (
    MarcadorDesconhecido,
    gerar_numeros_canonicos,
    gerar_numeros_tex,
    preencher_readme,
    textos_do_relatorio_de_avaliacao,
    usos,
)

BASE = config.PROJETO / "README.base.md"
RELATORIO_DE_AVALIACAO_DO_PROJETO = config.na_raiz(config.RELATORIO, config.PROJETO)
README = config.RAIZ / "README.md"
CANONICOS = config.RAIZ / "NUMEROS_CANONICOS.md"
NUMEROS_TEX = config.RELATORIO / "numeros.tex"
AVISO = "<!-- GERADO por scripts/06_gerar_documentos.py a partir de README.base.md. Não edite à mão. -->\n"


def textos_tex() -> dict[str, str]:
    """Os .tex escritos à mão, do projeto (sem numeros.tex nem as linhas de tabela de relatorio/tabelas/).

    Como o README.base.md, eles são código: uma raiz temporária não tem cópia
    deles, e o pdflatex compila o do projeto com as entradas da raiz.
    """
    return textos_do_relatorio_de_avaliacao(RELATORIO_DE_AVALIACAO_DO_PROJETO, config.PROJETO)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    registro = numeros.carregar()
    base = BASE.read_text(encoding="utf-8")
    try:
        readme = AVISO + preencher_readme(base, registro)
    except MarcadorDesconhecido as erro:
        print(f"README não gerado: {erro.args[0]}")
        return 1

    config.RELATORIO.mkdir(parents=True, exist_ok=True)
    NUMEROS_TEX.write_text(gerar_numeros_tex(registro), encoding="utf-8", newline="\n")
    CANONICOS.write_text(
        gerar_numeros_canonicos(registro, usos(registro, base, textos_tex())), encoding="utf-8", newline="\n"
    )
    README.write_text(readme, encoding="utf-8", newline="\n")
    print(f"{len(registro)} números -> {NUMEROS_TEX.name}, {CANONICOS.name}, {README.name} (em {config.RAIZ})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Passo 6: gera relatorio/numeros.tex, NUMEROS_CANONICOS.md e README.md.

POR QUE ISTO EXISTE. Nenhum número impresso é digitado (ADR 0003). Este passo
lê o registro resultados/numeros.json, que cada script alimenta, e escreve as
três saídas. Para mudar o texto do README, edite README.base.md, e não o
README.md.

Uso: uv run python scripts/06_gerar_documentos.py
"""

import sys

from rag_sus import config, numeros
from rag_sus.documentos import gerar_numeros_canonicos, gerar_numeros_tex, preencher_readme, usos

BASE = config.RAIZ / "README.base.md"
README = config.RAIZ / "README.md"
CANONICOS = config.RAIZ / "NUMEROS_CANONICOS.md"
NUMEROS_TEX = config.RELATORIO / "numeros.tex"


def textos_tex() -> dict[str, str]:
    return {
        str(p.relative_to(config.RAIZ)).replace("\\", "/"): p.read_text(encoding="utf-8")
        for p in sorted(config.RELATORIO.rglob("*.tex"))
        if p.name != "numeros.tex"
    }


def main() -> int:
    registro = numeros.carregar()
    base = BASE.read_text(encoding="utf-8")

    config.RELATORIO.mkdir(parents=True, exist_ok=True)
    NUMEROS_TEX.write_text(gerar_numeros_tex(registro), encoding="utf-8", newline="\n")
    CANONICOS.write_text(
        gerar_numeros_canonicos(registro, usos(registro, base, textos_tex())), encoding="utf-8", newline="\n"
    )
    aviso = "<!-- GERADO por scripts/06_gerar_documentos.py a partir de README.base.md. Não edite à mão. -->\n"
    README.write_text(aviso + preencher_readme(base, registro), encoding="utf-8", newline="\n")
    print(f"{len(registro)} números -> {NUMEROS_TEX.name}, {CANONICOS.name}, {README.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

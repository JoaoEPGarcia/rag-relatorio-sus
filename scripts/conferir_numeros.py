# -*- coding: utf-8 -*-
"""Conferidor: nenhum número impresso foi digitado à mão, e os gerados estão em dia.

POR QUE ISTO EXISTE. A regra dos números só vale se alguém conferir. Este
script falha (código 1) se:
  1. README.md difere do que README.base.md + registro geram (edição à mão);
  2. README.base.md tem número digitado no texto corrido;
  3. o .tex do Relatório de avaliação tem número digitado no texto corrido;
  4. relatorio/numeros.tex ou NUMEROS_CANONICOS.md estão desatualizados;
  5. o .tex usa uma macro \\Num... que o registro não define.

Uso: uv run python scripts/conferir_numeros.py
"""

import importlib.util
import re
import sys

from rag_sus import config, numeros
from rag_sus.documentos import (
    digitos_soltos_no_markdown,
    digitos_soltos_no_tex,
    gerar_numeros_canonicos,
    gerar_numeros_tex,
    nome_macro,
    preencher_readme,
    usos,
)

_espec = importlib.util.spec_from_file_location("gerar", config.RAIZ / "scripts" / "06_gerar_documentos.py")
gerar = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(gerar)


def main() -> int:
    falhas: list[str] = []
    registro = numeros.carregar()
    base = gerar.BASE.read_text(encoding="utf-8")

    readme = gerar.README.read_text(encoding="utf-8") if gerar.README.exists() else ""
    if preencher_readme(base, registro) not in readme:
        falhas.append("README.md difere do gerado: edite README.base.md e rode scripts/06_gerar_documentos.py")

    soltos = digitos_soltos_no_markdown(base)
    if soltos:
        falhas.append(f"README.base.md tem número digitado: {soltos[:10]}")

    tex = gerar.textos_tex()
    for nome, texto in tex.items():
        soltos = digitos_soltos_no_tex(texto)
        if soltos:
            falhas.append(f"{nome} tem número digitado no texto: {soltos[:10]}")
        definidas = {nome_macro(c) for c in registro}
        for macro in sorted(set(re.findall(r"\\(Num[A-Z][A-Za-z]*)", texto)) - definidas):
            falhas.append(f"{nome} usa \\{macro}, que o registro não define")

    if not gerar.NUMEROS_TEX.exists() or gerar.NUMEROS_TEX.read_text(encoding="utf-8") != gerar_numeros_tex(registro):
        falhas.append("relatorio/numeros.tex desatualizado: rode scripts/06_gerar_documentos.py")
    esperado = gerar_numeros_canonicos(registro, usos(registro, base, tex))
    if not gerar.CANONICOS.exists() or gerar.CANONICOS.read_text(encoding="utf-8") != esperado:
        falhas.append("NUMEROS_CANONICOS.md desatualizado: rode scripts/06_gerar_documentos.py")

    for f in falhas:
        print(f"FALHA: {f}")
    print("Conferência dos números: " + ("ok" if not falhas else f"{len(falhas)} falha(s)"))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())

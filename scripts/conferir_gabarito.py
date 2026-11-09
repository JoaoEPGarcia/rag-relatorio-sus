# -*- coding: utf-8 -*-
"""Conferência mecânica do Gabarito contra o texto extraído (não substitui a Revisão).

POR QUE ISTO EXISTE. Antes de o autor conferir cada linha no PDF, uma checagem
automática pega os erros grosseiros: formato inválido, página fora do
corpus, valor numérico que não aparece no texto da página citada. O que ela
não pega (pergunta ambígua, resposta certa na página errada mas com o mesmo
número, número que só existe na imagem) é trabalho da Revisão.

Uso: uv run python scripts/conferir_gabarito.py [caminho.csv]
"""

import sys
from pathlib import Path

from rag_sus import config
from rag_sus.avaliacao.gabarito import carregar_gabarito
from rag_sus.avaliacao.pontuacao import extrair_numeros
from rag_sus.extracao import extrair_paginas


def main() -> int:
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else config.GABARITO
    itens = carregar_gabarito(caminho, exigir_revisao=False)
    paginas = {p.pagina_impressa: " ".join(b.texto for b in p.blocos) for p in extrair_paginas(config.PDF)}

    problemas = 0
    for item in itens:
        for pagina in item.paginas:
            if pagina not in paginas:
                print(f"{item.id}: página {pagina} fora do corpus")
                problemas += 1
        presentes = [n for pg in item.paginas if pg in paginas for n in extrair_numeros(paginas[pg])]
        for valor in item.valores:
            if not any(abs(valor - n) < 1e-9 for n in presentes):
                print(f"{item.id}: valor {valor} não aparece nas páginas {list(item.paginas)}")
                problemas += 1

    revisadas = sum(1 for i in itens if i.revisado)
    print(f"{len(itens)} linhas, {revisadas} revisadas, {problemas} problema(s) mecânico(s)")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())

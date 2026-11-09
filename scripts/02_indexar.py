# -*- coding: utf-8 -*-
"""Passo 2: calcula os embeddings dos Trechos e grava o índice FAISS.

POR QUE ISTO EXISTE. O índice é derivado (não vai para o git) e leva alguns
minutos na CPU; separado da extração, ele só é refeito quando os Trechos ou
o modelo mudam. Na primeira vez, baixa o multilingual-e5-large (2,24 GB)
para a pasta modelos/.

Uso: uv run python scripts/02_indexar.py
"""

import json
import sys
import time

from rag_sus import config
from rag_sus.busca import E5Embutidor, IndiceDeTrechos
from rag_sus.modelos import Trecho


def main() -> int:
    with open(config.TRECHOS, encoding="utf-8") as f:
        trechos = [Trecho.de_dict(json.loads(l)) for l in f if l.strip()]

    inicio = time.perf_counter()
    embutidor = E5Embutidor(pasta_cache=config.CACHE_MODELOS)
    indice = IndiceDeTrechos.construir(trechos, embutidor)
    indice.salvar(config.INDICE)
    print(f"{len(trechos)} Trechos indexados em {time.perf_counter() - inicio:.0f} s -> {config.INDICE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

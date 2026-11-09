# -*- coding: utf-8 -*-
"""Passo 1: extrai o Relatório-fonte e o quebra em Trechos.

POR QUE ISTO EXISTE. Tudo o que vem depois (índice, Condições, avaliação)
parte dos Trechos. Eles ficam versionados em dados/trechos.jsonl para que a
avaliação possa ser conferida sem reextrair o PDF, e para que uma mudança na
extração apareça no diff. Grava também o texto completo, usado pela Condição
contexto completo, e os números do corpus no registro.

Uso: uv run python scripts/01_extrair.py
"""

import json
import sys
from collections import Counter

from rag_sus import config
from rag_sus.extracao import extrair_paginas
from rag_sus.numeros import registrar
from rag_sus.quebra import contar_palavras, quebrar

ESTE_SCRIPT = "scripts/01_extrair.py"


def main() -> int:
    parametros = config.carregar_parametros()
    paginas = extrair_paginas(config.PDF)
    trechos = quebrar(paginas, parametros.alvo_palavras, parametros.sobreposicao_palavras)

    config.TRECHOS.parent.mkdir(parents=True, exist_ok=True)
    with open(config.TRECHOS, "w", encoding="utf-8", newline="\n") as f:
        for t in trechos:
            f.write(json.dumps(t.para_dict(), ensure_ascii=False) + "\n")

    # Texto completo para a Condição contexto completo: cada página marcada
    # com a página impressa, para o modelo poder citar.
    partes = []
    for p in paginas:
        corpo = "\n\n".join(b.texto for b in p.blocos)
        partes.append(f"[página {p.pagina_impressa}]\n{corpo}")
    config.TEXTO_COMPLETO.write_text("\n\n".join(partes) + "\n", encoding="utf-8", newline="\n")

    por_tipo = Counter(t.tipo for t in trechos)
    palavras = sum(contar_palavras(b.texto) for p in paginas for b in p.blocos)
    tabelas = sum(1 for p in paginas for b in p.blocos if b.tipo == "tabela")
    legendas = sum(1 for p in paginas for b in p.blocos if b.tipo == "legenda")

    registrar("corpus_paginas", len(paginas), "páginas do Relatório-fonte no corpus (sem a capa)", ESTE_SCRIPT)
    registrar("corpus_palavras", palavras, "palavras extraídas do Relatório-fonte", ESTE_SCRIPT)
    registrar("corpus_trechos", len(trechos), "Trechos indexados", ESTE_SCRIPT)
    registrar("corpus_trechos_texto", por_tipo["texto"], "Trechos de texto corrido", ESTE_SCRIPT)
    registrar("corpus_trechos_tabela", por_tipo["tabela"], "Trechos de tabela", ESTE_SCRIPT)
    registrar("corpus_trechos_legenda", por_tipo["legenda"], "Trechos de legenda de figura", ESTE_SCRIPT)
    registrar("corpus_tabelas", tabelas, "tabelas extraídas (blocos de tabela)", ESTE_SCRIPT)
    registrar("corpus_legendas", legendas, "legendas de figura extraídas", ESTE_SCRIPT)
    registrar("quebra_alvo", parametros.alvo_palavras, "máximo de palavras por Trecho de texto", ESTE_SCRIPT)
    registrar(
        "quebra_sobreposicao", parametros.sobreposicao_palavras,
        "máximo de palavras repetidas entre Trechos vizinhos", ESTE_SCRIPT,
    )

    print(f"{len(paginas)} páginas, {palavras} palavras, {len(trechos)} Trechos {dict(por_tipo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

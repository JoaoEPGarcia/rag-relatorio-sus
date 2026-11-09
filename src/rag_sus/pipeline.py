# -*- coding: utf-8 -*-
"""O pipeline completo: da extração à conferência, na ordem, parando no primeiro erro.

POR QUE ISTO EXISTE. Quem clona o repositório precisa refazer tudo com um
comando, sem chamar o modelo e a partir das Rodadas versionadas. Este módulo
diz quais passos rodam, em que ordem, e quais são pulados (e por quê); a
casca scripts/reproduzir.py liga cada passo ao script de verdade. A Rodada
paga (scripts/03_rodar_avaliacao.py) nunca é um passo.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rag_sus.avaliacao.sinteticas import rodada_sintetica


# O que a extração e o índice gravam, relativo à raiz (os mesmos caminhos de config).
# Se tudo existe, o passo é pulado: o índice exige o modelo de embeddings de 2,24 GB.
EXTRAIDOS = ("dados/trechos.jsonl", "dados/texto_completo.txt")
INDEXADOS = ("indice/indice.faiss", "indice/meta.json")


def _todos_existem(raiz: Path, relativos: tuple[str, ...]) -> bool:
    return all((raiz / r).exists() for r in relativos)


@dataclass(frozen=True)
class Passo:
    nome: str
    executar: Callable[[], int]
    # Motivo para não rodar; None quando o passo roda.
    pulado: str | None = None


def passos_do_pipeline(
    raiz: Path, rodar_script: Callable[[str], int], compilar: Callable[[], int]
) -> list[Passo]:
    """Os passos sobre a raiz, na ordem. rodar_script recebe o nome do script em scripts/."""

    def script(nome: str) -> Callable[[], int]:
        return lambda: rodar_script(nome)

    extrair = not _todos_existem(raiz, EXTRAIDOS)
    indexar = extrair or not _todos_existem(raiz, INDEXADOS)
    so_pdf_real = None
    if rodada_sintetica(raiz / "resultados" / "rodadas" / "principal"):
        # Rodadas sintéticas: Gabarito sintético, e os números do corpus copiados do
        # registro do projeto. Nada aqui lê o PDF real, os Trechos ou o índice.
        extrair = indexar = False
        so_pdf_real = "Rodadas sintéticas: a raiz não tem o PDF real nem o Gabarito"
    return [
        Passo("extração", script("01_extrair.py"),
              None if extrair else so_pdf_real or "os Trechos já existem"),
        Passo("índice", script("02_indexar.py"), None if indexar else so_pdf_real or "o índice já existe"),
        Passo("análise", script("04_analisar.py")),
        Passo("figuras", script("05_figuras.py")),
        Passo("documentos", script("06_gerar_documentos.py")),
        Passo("compilação do Relatório de avaliação", compilar),
        Passo("conferidor de números", script("conferir_numeros.py")),
        Passo("conferência do Gabarito", script("conferir_gabarito.py"), so_pdf_real),
    ]


def rodar(passos: list[Passo]) -> int:
    """Roda os passos na ordem; no primeiro que falhar, diz qual foi e devolve o código dele (≠ 0)."""
    for passo in passos:
        if passo.pulado:
            print(f"== {passo.nome}: pulado ({passo.pulado})", flush=True)
            continue
        print(f"== {passo.nome}", flush=True)
        try:
            codigo = passo.executar()
        except Exception as erro:  # um passo que quebra também para o pipeline, com o nome dele
            print(f"{type(erro).__name__}: {erro}")
            codigo = 1
        if codigo != 0:
            print(f"Pipeline parado no passo «{passo.nome}» (código {codigo}).")
            return codigo
    print("Pipeline completo.")
    return 0

# -*- coding: utf-8 -*-
"""Caminhos do projeto e leitura de parametros.toml e do .env.

POR QUE ISTO EXISTE. Os scripts, a API e os testes precisam concordar sobre
onde ficam o PDF, os Trechos, o índice e os resultados, e sobre os
parâmetros congelados. Um lugar só evita caminhos repetidos e divergentes.
As credenciais vêm só do ambiente (.env local, fora do git).
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

# PROJETO é a cópia do código (scripts/, README.base.md); RAIZ é onde ficam os
# dados e as saídas. São a mesma pasta, salvo quando RAG_SUS_RAIZ aponta para
# uma raiz temporária (as Rodadas sintéticas de demonstração, por exemplo).
PROJETO = Path(__file__).resolve().parents[2]
RAIZ = Path(os.environ.get("RAG_SUS_RAIZ", PROJETO))

PDF = RAIZ / "dados" / "relatorio_fonte.pdf"
TRECHOS = RAIZ / "dados" / "trechos.jsonl"
TEXTO_COMPLETO = RAIZ / "dados" / "texto_completo.txt"
INDICE = RAIZ / "indice"
CACHE_MODELOS = Path(os.environ.get("RAG_SUS_CACHE_MODELOS", RAIZ / "modelos"))
PARAMETROS = RAIZ / "parametros.toml"

AVALIACAO = RAIZ / "avaliacao"
GABARITO = AVALIACAO / "gabarito.csv"
PERGUNTAS_DESENVOLVIMENTO = AVALIACAO / "perguntas_desenvolvimento.csv"
REVISAO_VEREDICTOS = AVALIACAO / "revisao_veredictos.csv"

RESULTADOS = RAIZ / "resultados"
RODADAS = RESULTADOS / "rodadas"
NUMEROS = RESULTADOS / "numeros.json"
FIGURAS = RAIZ / "figuras"
RELATORIO = RAIZ / "relatorio"
# Linhas das tabelas do Relatório de avaliação, escritas por script e lidas com \linhasde.
TABELAS = RELATORIO / "tabelas"
TEX_DO_RELATORIO = RELATORIO / "relatorio.tex"


def na_raiz(caminho: Path, raiz: Path) -> Path:
    """O mesmo caminho de cima, mas sob outra raiz: `na_raiz(RODADAS, PROJETO)`, por exemplo.

    Para quem precisa de um caminho de uma raiz que não é a RAIZ desta
    execução (o gerador das Rodadas sintéticas grava numa raiz passada como
    argumento; o .tex e o registro do projeto são lidos mesmo sob RAG_SUS_RAIZ).
    """
    return Path(raiz) / Path(caminho).relative_to(RAIZ)


@dataclass(frozen=True)
class Parametros:
    congelado: bool
    alvo_palavras: int
    sobreposicao_palavras: int
    modelo_embeddings: str
    k: int
    modelo_respondedor: str
    esforco_respondedor: str
    max_tokens_respondedor: int
    modelo_juiz: str
    esforco_juiz: str
    max_tokens_juiz: int
    repeticoes: int


def carregar_parametros(caminho: Path = PARAMETROS) -> Parametros:
    with open(caminho, "rb") as f:
        p = tomllib.load(f)
    return Parametros(
        congelado=p["estado"]["congelado"],
        alvo_palavras=p["quebra"]["alvo_palavras"],
        sobreposicao_palavras=p["quebra"]["sobreposicao_palavras"],
        modelo_embeddings=p["busca"]["modelo_embeddings"],
        k=p["busca"]["k"],
        modelo_respondedor=p["respondedor"]["modelo"],
        esforco_respondedor=p["respondedor"]["esforco"],
        max_tokens_respondedor=p["respondedor"]["max_tokens"],
        modelo_juiz=p["juiz"]["modelo"],
        esforco_juiz=p["juiz"]["esforco"],
        max_tokens_juiz=p["juiz"]["max_tokens"],
        repeticoes=p["avaliacao"]["repeticoes"],
    )


def carregar_env() -> None:
    """Lê o .env da raiz, se existir. Variáveis já definidas no ambiente vencem."""
    from dotenv import load_dotenv

    load_dotenv(RAIZ / ".env", override=False)

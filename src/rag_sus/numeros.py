# -*- coding: utf-8 -*-
"""Registro único dos números impressos, e a forma de escrevê-los em português.

POR QUE ISTO EXISTE. A regra do portfólio: todo número impresso (README,
Relatório de avaliação, figuras) sai de um script e fica listado em
NUMEROS_CANONICOS.md. Cada script que calcula um número o grava aqui, com o
texto já formatado em português (vírgula decimal, ponto de milhar). O
scripts/06_gerar_documentos.py lê este registro e gera relatorio/numeros.tex,
NUMEROS_CANONICOS.md e README.md (ADR 0003). Ninguém digita número.

O arquivo é ordenado por chave e não guarda data, para que rodar de novo sem
mudança nenhuma não gere diff.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from rag_sus import config

_CHAVE = re.compile(r"^[a-z][a-z0-9_]*$")
_MENOS = "−"  # sinal de menos tipográfico


def _milhar(inteiro: int) -> str:
    return f"{inteiro:,}".replace(",", ".")


def _decimal(valor: float, casas: int) -> str:
    texto = f"{abs(valor):,.{casas}f}"
    texto = texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return (_MENOS if valor < 0 else "") + texto


def formatar(valor: float | int, formato: str) -> str:
    """Escreve o número em português.

    Formatos: inteiro, ano, decN (N casas), pct1 (proporção como %), pp1
    (diferença de proporções em pontos percentuais), p3 (valor-p), usd2.
    """
    if formato == "inteiro":
        return (_MENOS if valor < 0 else "") + _milhar(abs(int(round(valor))))
    if formato == "ano":
        return str(int(valor))
    if formato.startswith("dec") and formato[3:].isdigit():
        return _decimal(float(valor), int(formato[3:]))
    if formato == "pct1":
        return _decimal(100 * float(valor), 1) + "%"
    if formato == "pp1":
        return _decimal(100 * float(valor), 1) + " p.p."
    if formato == "p3":
        return "< 0,001" if valor < 0.001 else _decimal(float(valor), 3)
    if formato == "usd2":
        return "US$ " + _decimal(float(valor), 2)
    raise ValueError(f"formato desconhecido: {formato}")


def carregar(caminho: Path | None = None) -> dict[str, dict]:
    caminho = caminho or config.NUMEROS
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def registrar(
    chave: str,
    valor: float | int,
    descricao: str,
    script: str,
    formato: str | None = None,
    caminho: Path | None = None,
) -> str:
    """Grava (ou substitui) um número no registro e devolve o texto formatado."""
    if not _CHAVE.match(chave):
        raise ValueError(f"chave '{chave}' inválida: use minúsculas, dígitos e _")
    if formato is None:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ValueError(f"{chave}: número não inteiro precisa de formato explícito")
        formato = "inteiro"
    caminho = caminho or config.NUMEROS
    dados = carregar(caminho)
    texto = formatar(valor, formato)
    dados[chave] = {
        "valor": valor,
        "texto": texto,
        "descricao": descricao,
        "script": script,
        "formato": formato,
    }
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dict(sorted(dados.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return texto

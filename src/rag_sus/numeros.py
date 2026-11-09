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
from collections.abc import Iterable
from dataclasses import dataclass
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


@dataclass(frozen=True)
class Numero:
    """Um número a registrar. `aparece_em` declara onde ele é impresso fora do .tex e do README."""

    chave: str
    valor: float | int
    descricao: str
    formato: str | None = None
    aparece_em: tuple[str, ...] = ()


def _entrada(n: Numero, script: str) -> dict:
    if not _CHAVE.match(n.chave):
        raise ValueError(f"chave '{n.chave}' inválida: use minúsculas, dígitos e _")
    formato = n.formato
    if formato is None:
        if isinstance(n.valor, bool) or not isinstance(n.valor, int):
            raise ValueError(f"{n.chave}: número não inteiro precisa de formato explícito")
        formato = "inteiro"
    entrada = {
        "valor": n.valor,
        "texto": formatar(n.valor, formato),
        "descricao": n.descricao,
        "script": script,
        "formato": formato,
    }
    if n.aparece_em:
        entrada["aparece_em"] = list(n.aparece_em)
    return entrada


def _gravar(dados: dict[str, dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dict(sorted(dados.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def registrar(
    chave: str,
    valor: float | int,
    descricao: str,
    script: str,
    formato: str | None = None,
    caminho: Path | None = None,
) -> str:
    """Grava (ou substitui) um número no registro e devolve o texto formatado."""
    entrada = _entrada(Numero(chave, valor, descricao, formato), script)
    caminho = caminho or config.NUMEROS
    dados = carregar(caminho)
    dados[chave] = entrada
    _gravar(dados, caminho)
    return entrada["texto"]


def registrar_do_script(script: str, lista: Iterable[Numero], caminho: Path | None = None) -> dict[str, str]:
    """Substitui de uma vez todos os números de um script e devolve chave -> texto.

    Os números que o script gravou antes e não estão em `lista` saem do
    registro: um resultado que deixou de existir (uma repetição apagada, por
    exemplo) não fica para trás com o valor velho. Os números dos outros
    scripts ficam como estão.
    """
    novos: dict[str, dict] = {}
    for n in lista:
        if n.chave in novos:
            raise ValueError(f"chave repetida no lote de {script}: {n.chave}")
        novos[n.chave] = _entrada(n, script)
    caminho = caminho or config.NUMEROS
    dados = {c: e for c, e in carregar(caminho).items() if e.get("script") != script}
    dados.update(novos)
    _gravar(dados, caminho)
    return {c: e["texto"] for c, e in novos.items()}

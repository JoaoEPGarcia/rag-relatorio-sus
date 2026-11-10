# -*- coding: utf-8 -*-
"""Registro único dos números impressos, e a forma de escrevê-los em português.

POR QUE ISTO EXISTE. A regra do portfólio: todo número impresso (README,
Relatório de avaliação, figuras) sai de um script e fica listado em
NUMEROS_CANONICOS.md. Cada script que calcula um número o grava aqui, com o
texto já formatado em português (vírgula decimal, ponto de milhar) em
"texto" e em inglês (ponto decimal, vírgula de milhar) em "texto_en", este
para a seção "In English" do README. O
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


IDIOMAS = ("pt", "en")
# Onde outro script imprime um número que não é dele: {script: [lugares]}, dentro da entrada do número.
USOS = "usos_declarados"
_PONTOS_PERCENTUAIS = {"pt": " p.p.", "en": " pp"}


def _decimal(valor: float, casas: int, idioma: str) -> str:
    """Separador de milhar e vírgula decimal em português; vírgula de milhar e ponto em inglês."""
    texto = f"{abs(valor):,.{casas}f}"
    if idioma == "pt":
        texto = texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return (_MENOS if valor < 0 else "") + texto


def formatar(valor: float | int, formato: str, idioma: str = "pt") -> str:
    """Escreve o número em português (padrão) ou em inglês (`idioma="en"`).

    Formatos: inteiro, ano, decN (N casas), pct1 (proporção como %), pp1
    (diferença de proporções em pontos percentuais), p3 (valor-p), usd2.
    O sinal de menos é o tipográfico nos dois idiomas.
    """
    if idioma not in IDIOMAS:
        raise ValueError(f"idioma desconhecido: {idioma}")
    if formato == "inteiro":
        return _decimal(int(round(valor)), 0, idioma)
    if formato == "ano":
        return str(int(valor))
    if formato.startswith("dec") and formato[3:].isdigit():
        return _decimal(float(valor), int(formato[3:]), idioma)
    if formato == "pct1":
        return _decimal(100 * float(valor), 1, idioma) + "%"
    if formato == "pp1":
        return _decimal(100 * float(valor), 1, idioma) + _PONTOS_PERCENTUAIS[idioma]
    if formato == "p3":
        return "< " + _decimal(0.001, 3, idioma) if valor < 0.001 else _decimal(float(valor), 3, idioma)
    if formato == "usd2":
        return "US$ " + _decimal(float(valor), 2, idioma)
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


@dataclass(frozen=True)
class Texto:
    """Um texto que o script escolhe a partir do resultado, em português e em inglês.

    Serve para a frase que depende do sinal ou do tamanho de um número (o
    IC da diferença inclui o zero ou não; qual Classe de erro é a mais
    frequente), para que o README nunca afirme um achado que o resultado não
    sustenta. Entra no registro com formato "texto" e vira marcador e macro
    como qualquer número.
    """

    chave: str
    texto: str
    texto_en: str
    descricao: str


def _entrada(n: Numero | Texto, script: str) -> dict:
    if not _CHAVE.match(n.chave):
        raise ValueError(f"chave '{n.chave}' inválida: use minúsculas, dígitos e _")
    if isinstance(n, Texto):
        return {"valor": n.texto, "texto": n.texto, "texto_en": n.texto_en, "descricao": n.descricao,
                "script": script, "formato": "texto"}
    formato = n.formato
    if formato is None:
        if isinstance(n.valor, bool) or not isinstance(n.valor, int):
            raise ValueError(f"{n.chave}: número não inteiro precisa de formato explícito")
        formato = "inteiro"
    entrada = {
        "valor": n.valor,
        "texto": formatar(n.valor, formato),
        "texto_en": formatar(n.valor, formato, idioma="en"),
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
    aparece_em: Iterable[str] = (),
) -> str:
    """Grava (ou substitui) um número no registro e devolve o texto formatado.

    `aparece_em` declara onde o número é impresso fora do README e do .tex
    (uma figura, por exemplo), para a coluna "Onde aparece" do
    NUMEROS_CANONICOS.md.
    """
    entrada = _entrada(Numero(chave, valor, descricao, formato, tuple(aparece_em)), script)
    caminho = caminho or config.NUMEROS
    dados = carregar(caminho)
    if USOS in dados.get(chave, {}):
        entrada[USOS] = dados[chave][USOS]
    dados[chave] = entrada
    _gravar(dados, caminho)
    return entrada["texto"]


def registrar_do_script(
    script: str, lista: Iterable[Numero | Texto], caminho: Path | None = None
) -> dict[str, str]:
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
    antigos = carregar(caminho)
    for chave, entrada in novos.items():
        # os usos que outro script declarou sobre um número deste ficam (as figuras, por exemplo)
        if USOS in antigos.get(chave, {}):
            entrada[USOS] = antigos[chave][USOS]
    dados = {c: e for c, e in antigos.items() if e.get("script") != script}
    dados.update(novos)
    _gravar(dados, caminho)
    return {c: e["texto"] for c, e in novos.items()}


def declarar_usos(script: str, usos: dict[str, Iterable[str]], caminho: Path | None = None) -> None:
    """Declara onde `script` imprime números que outro script registrou, sem copiá-los.

    É como uma figura diz que imprime o acerto do scripts/04_analisar.py: o
    número continua um só, do dono, e o lugar entra na coluna "Onde aparece"
    do NUMEROS_CANONICOS.md. Os usos ficam guardados sob o script que os
    declarou, numa vez só: os que ele declarou antes e não estão em `usos`
    saem, e os dos outros ficam. Sobrevivem a uma nova execução do dono
    (registrar_do_script os preserva). Chave que o registro não tem é erro.
    """
    caminho = caminho or config.NUMEROS
    dados = carregar(caminho)
    faltam = sorted(set(usos) - set(dados))
    if faltam:
        raise KeyError(f"{script} declara uso de números que o registro não tem: {', '.join(faltam)}")
    for entrada in dados.values():
        entrada.get(USOS, {}).pop(script, None)
        if USOS in entrada and not entrada[USOS]:
            del entrada[USOS]
    for chave, lugares in usos.items():
        lugares = list(dict.fromkeys(lugares))
        if lugares:
            dados[chave].setdefault(USOS, {})[script] = lugares
    _gravar(dados, caminho)

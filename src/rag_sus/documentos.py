# -*- coding: utf-8 -*-
"""Geração do README, das macros LaTeX e do NUMEROS_CANONICOS.md a partir do registro.

POR QUE ISTO EXISTE. A regra do portfólio é que nenhum número impresso seja
digitado (ADR 0003). Este módulo transforma o registro resultados/numeros.json
em três saídas: relatorio/numeros.tex (macros \\NumXxx), README.md (a partir
de README.base.md, com marcadores {{chave}}) e NUMEROS_CANONICOS.md (uma
linha por número, nas colunas do kit). Traz também os conferidores que
procuram dígitos digitados à mão no Markdown e no LaTeX.
"""

from __future__ import annotations

import re
from pathlib import Path

_DIGITOS_POR_EXTENSO = {
    "0": "Zero", "1": "Um", "2": "Dois", "3": "Tres", "4": "Quatro",
    "5": "Cinco", "6": "Seis", "7": "Sete", "8": "Oito", "9": "Nove",
}
_MARCADOR = re.compile(r"\{\{\s*([a-z][a-z0-9_]*)\s*\}\}")


class MarcadorDesconhecido(KeyError):
    pass


def nome_macro(chave: str) -> str:
    """acerto_com_rag -> NumAcertoComRag. Macro LaTeX não aceita dígito: 1 -> Um."""
    partes = []
    for parte in chave.split("_"):
        parte = "".join(_DIGITOS_POR_EXTENSO.get(c, c) for c in parte)
        partes.append(parte[:1].upper() + parte[1:])
    return "Num" + "".join(partes)


def texto_tex(texto: str) -> str:
    """Escapa o que o pdfLaTeX não aceita no texto formatado em português."""
    return (
        texto.replace("\\", r"\textbackslash{}")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("\u2212", "$-$")
        .replace("< ", "$<$ ")
    )


def gerar_numeros_tex(registro: dict[str, dict]) -> str:
    linhas = [
        "% GERADO por scripts/06_gerar_documentos.py a partir de resultados/numeros.json.",
        "% Não edite à mão: mude o script que calcula o número e rode o pipeline de novo.",
    ]
    for chave in sorted(registro):
        linhas.append(f"\\newcommand{{\\{nome_macro(chave)}}}{{{texto_tex(registro[chave]['texto'])}}}")
    return "\n".join(linhas) + "\n"


def preencher_readme(base: str, registro: dict[str, dict]) -> str:
    def trocar(m: re.Match) -> str:
        chave = m.group(1)
        if chave not in registro:
            raise MarcadorDesconhecido(f"marcador {{{{{chave}}}}} não está em resultados/numeros.json")
        return registro[chave]["texto"]

    return _MARCADOR.sub(trocar, base)


# Arquivos de relatorio/ escritos por script, com dígitos de propósito: as macros
# (numeros.tex, por scripts/06_gerar_documentos.py) e as linhas de tabela lidas
# com \linhasde (tabelas/, por scripts/04_analisar.py). O conferidor não os lê.
GERADOS_NO_RELATORIO = ("numeros.tex",)
PASTAS_GERADAS_NO_RELATORIO = ("tabelas",)


def textos_do_relatorio(pasta_relatorio: Path, raiz: Path) -> dict[str, str]:
    """Os .tex escritos à mão no Relatório de avaliação, pelo caminho relativo à raiz."""
    textos = {}
    for p in sorted(pasta_relatorio.rglob("*.tex")):
        relativo = p.relative_to(pasta_relatorio)
        if relativo.name in GERADOS_NO_RELATORIO and len(relativo.parts) == 1:
            continue
        if relativo.parts[0] in PASTAS_GERADAS_NO_RELATORIO:
            continue
        textos[p.relative_to(raiz).as_posix()] = p.read_text(encoding="utf-8")
    return textos


def usos(registro: dict[str, dict], readme_base: str, textos_tex: dict[str, str]) -> dict[str, list[str]]:
    """Onde cada número aparece: README, cada .tex e o que o script declarou (figuras)."""
    no_readme = set(_MARCADOR.findall(readme_base))
    saida: dict[str, list[str]] = {}
    for chave, entrada in registro.items():
        lugares = []
        if chave in no_readme:
            lugares.append("README")
        padrao = re.compile(r"\\" + nome_macro(chave) + r"(?![A-Za-z])")
        lugares.extend(nome for nome, texto in textos_tex.items() if padrao.search(texto))
        lugares.extend(entrada.get("aparece_em", []))
        saida[chave] = lugares
    return saida


def gerar_numeros_canonicos(registro: dict[str, dict], onde: dict[str, list[str]]) -> str:
    linhas = [
        "# Números canônicos",
        "",
        "Cada número impresso no README, no Relatório de avaliação ou numa figura tem uma linha aqui, "
        "com o script que o calcula e os lugares onde aparece.",
        "",
        "**Arquivo gerado** por `scripts/06_gerar_documentos.py` a partir de `resultados/numeros.json`. "
        "Não edite à mão. Para mudar um número, mude o script da coluna \"Sai de\", rode o pipeline "
        "(`uv run python scripts/rodar_tudo.py`) e confira cada lugar da coluna \"Onde aparece\".",
        "",
        "| Número | Valor | O que é | Sai de | Onde aparece |",
        "|---|---|---|---|---|",
    ]
    for chave in sorted(registro):
        e = registro[chave]
        lugares = ", ".join(onde.get(chave, [])) or "(não impresso)"
        valor = e["texto"].replace("|", "\\|")
        linhas.append(f"| `\\{nome_macro(chave)}` | {valor} | {e['descricao']} | `{e['script']}` | {lugares} |")
    return "\n".join(linhas) + "\n"


# --------------------------------------------------------------------------
# Conferidores de dígitos digitados à mão
# --------------------------------------------------------------------------

_BLOCO_DE_CODIGO = re.compile(r"```.*?```", re.S)
_CODIGO_EM_LINHA = re.compile(r"`[^`]*`")
_LINK = re.compile(r"\]\([^)]*\)|<[^>]+>|https?://\S+")
_COMENTARIO_HTML = re.compile(r"<!--.*?-->", re.S)
_MARCADOR_DE_LISTA = re.compile(r"^\s*\d+\.\s", re.M)
_NUMERO_SOLTO = re.compile(r"(?<![A-Za-z_])\d+(?:[.,]\d+)*")


def digitos_soltos_no_markdown(texto: str) -> list[str]:
    """Números no texto corrido do Markdown, fora de código, links e marcadores."""
    for padrao in (_COMENTARIO_HTML, _BLOCO_DE_CODIGO, _CODIGO_EM_LINHA, _LINK, _MARCADOR, _MARCADOR_DE_LISTA):
        texto = padrao.sub(" ", texto)
    return _NUMERO_SOLTO.findall(texto)


_COMENTARIO_TEX = re.compile(r"(?<!\\)%.*")
_COMANDO_COM_ARGUMENTOS = re.compile(r"\\[A-Za-z@]+\*?(\[[^\]]*\])*(\{[^{}]*\})*")
_DIMENSAO = re.compile(r"\d+(?:\.\d+)?\s*(?:mm|cm|pt|em|ex)\b")


def digitos_soltos_no_tex(tex: str) -> list[str]:
    """Números no corpo do .tex fora de comandos, opções, argumentos e comentários.

    É uma heurística: argumentos de comando (rótulos, nomes de arquivo,
    medidas) são descartados inteiros. Texto em \\textbf{...} também é
    descartado, então números digitados dentro de comandos não são pegos;
    o que ela garante é o texto corrido limpo.
    """
    inicio = tex.find("\\begin{document}")
    corpo = tex[inicio:] if inicio >= 0 else tex
    corpo = _COMENTARIO_TEX.sub("", corpo)
    corpo = _DIMENSAO.sub(" ", corpo)
    anterior = None
    while anterior != corpo:
        anterior = corpo
        corpo = _COMANDO_COM_ARGUMENTOS.sub(" ", corpo)
    return _NUMERO_SOLTO.findall(corpo)

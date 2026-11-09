# -*- coding: utf-8 -*-
"""Quebra das páginas do Relatório-fonte em Trechos.

POR QUE ISTO EXISTE. A busca recupera Trechos, e a citação aponta a Página
do Trecho. Para a citação ser exata, nenhum Trecho atravessa a fronteira de
página. Dentro da página, o texto corrido se junta por parágrafo até um
tamanho-alvo (medido em palavras), com uma pequena sobreposição de frases
entre Trechos vizinhos, para que uma ideia cortada ao meio ainda apareça
inteira em algum deles. Tabela e legenda de figura viram Trechos próprios:
misturadas ao texto, as linhas de tabela diluiriam o vetor do parágrafo.

O título da seção abre cada Trecho, porque é ele que diz do que o número
trata ("63,2%" sozinho não diz nada; "Tabela 10 ... Filantrópico" diz).
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from rag_sus.modelos import Bloco, Pagina, TipoTrecho, Trecho

# Fim de frase: ponto, exclamação ou interrogação seguidos de espaço e de algo
# que começa frase (maiúscula, dígito, parêntese ou aspas). A vírgula decimal
# ("3,7%") não interfere; "R$ 4,3 bi. Em 2024" corta, como deve.
_FIM_DE_FRASE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9(\"“])")


def contar_palavras(texto: str) -> int:
    return len(texto.split())


def dividir_frases(texto: str) -> list[str]:
    return [f.strip() for f in _FIM_DE_FRASE.split(texto.strip()) if f.strip()]


def quebrar(paginas: Iterable[Pagina], alvo: int, sobreposicao: int) -> list[Trecho]:
    """Devolve os Trechos de todas as páginas, na ordem do documento.

    `alvo` é o máximo de palavras do corpo de um Trecho de texto (sem contar a
    linha da seção). `sobreposicao` é o máximo de palavras repetidas do fim de
    um Trecho no começo do seguinte, sempre em frases inteiras.
    """
    if sobreposicao >= alvo:
        raise ValueError(f"sobreposição ({sobreposicao}) precisa ser menor que o alvo ({alvo})")

    trechos: list[Trecho] = []
    for pagina in paginas:
        trechos.extend(_quebrar_pagina(pagina, alvo, sobreposicao))
    return trechos


def _quebrar_pagina(pagina: Pagina, alvo: int, sobreposicao: int) -> list[Trecho]:
    saida: list[Trecho] = []

    def emitir(tipo: TipoTrecho, corpo: str, secao: str) -> None:
        texto = f"{secao}\n{corpo}" if secao else corpo
        saida.append(
            Trecho(
                id=f"p{pagina.pagina_impressa:03d}-{len(saida):02d}",
                texto=texto,
                pagina_impressa=pagina.pagina_impressa,
                pagina_pdf=pagina.pagina_pdf,
                tipo=tipo,
                secao=secao,
            )
        )

    # Texto corrido acumulado: lista de (índice do parágrafo, frase).
    acumulado: list[tuple[int, str]] = []
    secao_atual: str | None = None

    def fechar() -> None:
        if acumulado:
            emitir("texto", _juntar(acumulado), secao_atual or "")

    def recomecar_com_sobreposicao() -> None:
        cauda: list[tuple[int, str]] = []
        palavras = 0
        for item in reversed(acumulado):
            n = contar_palavras(item[1])
            if palavras + n > sobreposicao:
                break
            cauda.insert(0, item)
            palavras += n
        acumulado[:] = cauda

    for i, bloco in enumerate(pagina.blocos):
        if bloco.tipo != "paragrafo":
            fechar()
            acumulado.clear()
            secao_atual = None
            _emitir_bloco_proprio(bloco, alvo, emitir)
            continue

        if secao_atual is not None and bloco.secao != secao_atual:
            fechar()
            acumulado.clear()
        secao_atual = bloco.secao

        # Parágrafo que cabe no alvo vai inteiro: se não cabe no que já está
        # acumulado, fecha-se o Trecho antes, em vez de partir o parágrafo.
        n_paragrafo = contar_palavras(bloco.texto)
        if acumulado and n_paragrafo <= alvo and _palavras(acumulado) + n_paragrafo > alvo:
            fechar()
            recomecar_com_sobreposicao()
            if _palavras(acumulado) + n_paragrafo > alvo:
                acumulado.clear()

        for frase in _frases_que_cabem(bloco.texto, alvo):
            n = contar_palavras(frase)
            if acumulado and _palavras(acumulado) + n > alvo:
                fechar()
                recomecar_com_sobreposicao()
                if acumulado and _palavras(acumulado) + n > alvo:
                    acumulado.clear()
            acumulado.append((i, frase))

    fechar()
    return saida


def _emitir_bloco_proprio(bloco: Bloco, alvo: int, emitir) -> None:
    if bloco.tipo == "tabela":
        for corpo in _partes_da_tabela(bloco.texto, alvo):
            emitir("tabela", corpo, bloco.secao)
        return

    # Legenda: um Trecho só, salvo se passar do alvo; aí, por frase, e o
    # rótulo ("Figura 5") acompanha cada parte para a parte não ficar órfã.
    frases = _frases_que_cabem(bloco.texto, alvo)
    rotulo = bloco.texto.split(":", 1)[0] if ":" in bloco.texto[:40] else ""
    partes: list[list[str]] = [[]]
    for frase in frases:
        if partes[-1] and contar_palavras(" ".join(partes[-1] + [frase])) > alvo:
            partes.append([])
        partes[-1].append(frase)
    for k, parte in enumerate(partes):
        corpo = " ".join(parte)
        if k > 0 and rotulo:
            corpo = f"{rotulo} (continuação): {corpo}"
        emitir("legenda", corpo, bloco.secao)


def _partes_da_tabela(texto: str, alvo: int) -> list[str]:
    """Divide uma tabela serializada por linha, repetindo a primeira linha.

    A primeira linha é a legenda da tabela ("Tabela 12: ..."); sem ela, uma
    parte com só "Hospital 37: escore 0,812" não diz de que lista se trata.
    """
    linhas = texto.split("\n")
    cabecalho, corpo = linhas[0], linhas[1:]
    if contar_palavras(texto) <= alvo or not corpo:
        return [texto]

    partes: list[str] = []
    atual: list[str] = []
    base = contar_palavras(cabecalho)
    for linha in corpo:
        if atual and base + contar_palavras("\n".join(atual + [linha])) > alvo:
            partes.append("\n".join([cabecalho, *atual]))
            atual = []
        atual.append(linha)
    if atual:
        partes.append("\n".join([cabecalho, *atual]))
    return partes


def _frases_que_cabem(texto: str, alvo: int) -> list[str]:
    """Frases do texto; uma frase maior que o alvo é cortada por palavra."""
    saida: list[str] = []
    for frase in dividir_frases(texto):
        palavras = frase.split()
        if len(palavras) <= alvo:
            saida.append(frase)
            continue
        for k in range(0, len(palavras), alvo):
            saida.append(" ".join(palavras[k : k + alvo]))
    return saida


def _palavras(acumulado: list[tuple[int, str]]) -> int:
    return sum(contar_palavras(f) for _, f in acumulado)


def _juntar(acumulado: list[tuple[int, str]]) -> str:
    """Frases do mesmo parágrafo separadas por espaço; parágrafos, por quebra de linha."""
    partes: list[str] = []
    anterior: int | None = None
    for indice, frase in acumulado:
        if anterior is None:
            partes.append(frase)
        elif indice == anterior:
            partes.append(" " + frase)
        else:
            partes.append("\n" + frase)
        anterior = indice
    return "".join(partes)

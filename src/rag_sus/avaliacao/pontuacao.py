# -*- coding: utf-8 -*-
"""Pontuação das respostas: regra numérica, citação, recuperação e Classes de erro.

POR QUE ISTO EXISTE. Metade do Gabarito é numérica ("quantas cirurgias em
2025?"). Para essas, o Veredicto não precisa de Juiz: basta conferir se os
números do Gabarito aparecem na resposta. A regra é estrita de propósito:
"45%" não acerta "44,7%", e "32.9%" (ponto decimal inglês) não acerta "32,9%",
porque o prompt manda copiar os números como estão no Relatório-fonte. Uma
resposta que a regra reprova vai também ao Juiz e à Revisão, para que um
falso negativo da regra não passe despercebido.

As Classes de erro saem das medidas, sem julgamento novo, e são mutuamente
exclusivas (docs/DESENHO.md).
"""

from __future__ import annotations

import re
from collections.abc import Sequence

# Número no formato brasileiro: milhar com ponto, decimal com vírgula, sinal
# opcional (hífen ou o sinal de menos tipográfico "−"). O sinal só conta se
# vier depois de espaço, parêntese ou do começo do texto: em "E3-4" o hífen
# separa, não nega.
_NUMERO = re.compile(
    r"(?:(?<![^\s(])([−-]))?"
    r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?(?!\d)"
)

TOLERANCIA = 1e-9


def extrair_numeros(texto: str) -> list[float]:
    numeros = []
    for sinal, inteiro, decimal in _NUMERO.findall(texto):
        valor = float(inteiro.replace(".", "") + (f".{decimal}" if decimal else ""))
        numeros.append(-valor if sinal else valor)
    return numeros


def acerto_numerico(resposta: str, esperados: Sequence[float]) -> bool:
    """Todos os números do Gabarito aparecem, exatamente, na resposta."""
    presentes = extrair_numeros(resposta)
    return all(any(abs(v - p) <= TOLERANCIA for p in presentes) for v in esperados)


def acerto_citacao(citadas: Sequence[int], gabarito: Sequence[int]) -> bool:
    """Alguma página citada está entre as páginas do Gabarito."""
    return bool(set(citadas) & set(gabarito))


def acerto_recuperacao(recuperadas: Sequence[int], gabarito: Sequence[int]) -> bool:
    """Alguma página do Gabarito está entre as páginas dos Trechos recuperados."""
    return bool(set(recuperadas) & set(gabarito))


def classificar_erro(
    acerto_resposta: bool,
    abstencao: bool,
    acerto_da_citacao: bool,
    acerto_da_recuperacao: bool | None,
    respondivel: bool,
) -> str | None:
    """Classe de erro de uma resposta, ou None se não houve erro.

    `acerto_da_recuperacao` é None nas Condições sem recuperação (sem RAG e
    contexto completo); nelas não existe falha de recuperação.
    """
    if not respondivel:
        return None if abstencao else "resposta inventada"
    if acerto_resposta:
        return None if acerto_da_citacao else "citação errada"
    if abstencao:
        return "abstenção indevida"
    if acerto_da_recuperacao is False:
        return "falha de recuperação"
    return "falha de leitura"

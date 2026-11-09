# -*- coding: utf-8 -*-
"""Contas estatísticas da avaliação: Wilson, McNemar exato e diferença pareada.

POR QUE ISTO EXISTE. Com 60 Perguntas, uma taxa de acerto sozinha engana: 48
em 60 (80%) é compatível com algo entre 68% e 88%. O intervalo de Wilson dá
essa faixa e, ao contrário do intervalo de Wald (p ± 1,96·EP), não sai de
[0, 1] nem colapsa quando o acerto é 0% ou 100%.

As Condições respondem às mesmas Perguntas, então as amostras são pareadas.
Comparar dois intervalos de Wilson como se fossem independentes desperdiça
essa informação. O teste exato de McNemar olha só os pares discordantes
(uma Condição acerta, a outra erra), e o intervalo de Newcombe (1998, método
10) dá a faixa da diferença pareada levando em conta a correlação entre as
duas Condições.

Referência: Newcombe, R. G. (1998). Improved confidence intervals for the
difference between binomial proportions based on paired data. Statistics in
Medicine, 17(22), 2635–2650.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from scipy.stats import binom, norm

NIVEL = 0.95


@dataclass(frozen=True)
class Intervalo:
    proporcao: float
    inferior: float
    superior: float


@dataclass(frozen=True)
class TabelaPareada:
    """Contagens das Perguntas por par de Veredictos (Condição A, Condição B)."""

    ambos: int  # as duas acertam
    so_a: int  # só A acerta
    so_b: int  # só B acerta
    nenhum: int  # as duas erram

    @property
    def n(self) -> int:
        return self.ambos + self.so_a + self.so_b + self.nenhum


@dataclass(frozen=True)
class DiferencaPareada:
    diferenca: float  # proporção de acerto de A menos a de B
    inferior: float
    superior: float


def _z(nivel: float) -> float:
    return float(norm.ppf(1 - (1 - nivel) / 2))


def wilson(acertos: int, n: int, nivel: float = NIVEL) -> Intervalo:
    """Intervalo de Wilson (escore) para uma proporção."""
    if n <= 0:
        raise ValueError("n precisa ser positivo")
    if not 0 <= acertos <= n:
        raise ValueError(f"acertos ({acertos}) fora de [0, {n}]")
    z = _z(nivel)
    p = acertos / n
    denominador = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / denominador
    meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominador
    return Intervalo(p, max(0.0, centro - meia), min(1.0, centro + meia))


def mcnemar_exato(so_a: int, so_b: int) -> float:
    """Valor-p bilateral do teste exato de McNemar (binomial nos discordantes)."""
    discordantes = so_a + so_b
    if discordantes == 0:
        return 1.0
    return float(min(1.0, 2 * binom.cdf(min(so_a, so_b), discordantes, 0.5)))


def tabela_pareada(acertos_a: Sequence[bool], acertos_b: Sequence[bool]) -> TabelaPareada:
    if len(acertos_a) != len(acertos_b):
        raise ValueError("as duas Condições precisam ter as mesmas Perguntas")
    pares = list(zip(acertos_a, acertos_b, strict=True))
    return TabelaPareada(
        ambos=sum(a and b for a, b in pares),
        so_a=sum(a and not b for a, b in pares),
        so_b=sum(b and not a for a, b in pares),
        nenhum=sum(not a and not b for a, b in pares),
    )


def diferenca_pareada(
    ambos: int, so_a: int, so_b: int, nenhum: int, nivel: float = NIVEL
) -> DiferencaPareada:
    """Diferença pareada de proporções com o intervalo de Newcombe (método 10)."""
    n = ambos + so_a + so_b + nenhum
    if n <= 0:
        raise ValueError("não há pares")
    p1 = (ambos + so_a) / n
    p2 = (ambos + so_b) / n
    i1 = wilson(ambos + so_a, n, nivel)
    i2 = wilson(ambos + so_b, n, nivel)

    produto = (ambos + so_a) * (so_b + nenhum) * (ambos + so_b) * (so_a + nenhum)
    phi = (ambos * nenhum - so_a * so_b) / math.sqrt(produto) if produto > 0 else 0.0

    d = p1 - p2
    abaixo = (p1 - i1.inferior) ** 2 - 2 * phi * (p1 - i1.inferior) * (i2.superior - p2) + (
        i2.superior - p2
    ) ** 2
    acima = (i1.superior - p1) ** 2 - 2 * phi * (i1.superior - p1) * (p2 - i2.inferior) + (
        p2 - i2.inferior
    ) ** 2
    inferior = d - math.sqrt(max(abaixo, 0.0))
    superior = d + math.sqrt(max(acima, 0.0))
    return DiferencaPareada(d, max(-1.0, inferior), min(1.0, superior))

# -*- coding: utf-8 -*-
"""Travas que impedem uma Rodada principal fora das regras do desenho.

POR QUE ISTO EXISTE. Duas regras do projeto só valem se forem verificadas por
código, e não por memória:

- ADR 0002: os parâmetros são congelados por commit antes da Rodada
  principal. Ajustá-los depois de ver os resultados sobre o Gabarito
  inflaria a taxa de acerto.
- A Revisão: nenhuma linha do Gabarito sem conferência do autor no PDF
  (essa trava está em gabarito.carregar_gabarito).

As Rodadas de desenvolvimento não passam por estas travas e nunca entram nos
números publicados.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

RODADAS_PUBLICADAS = ("principal", "repeticao1", "repeticao2")
RODADAS = ("desenvolvimento", *RODADAS_PUBLICADAS)


class ParametrosNaoCongelados(RuntimeError):
    pass


def verificar_congelamento(congelado: bool, mudancas_nao_commitadas: str) -> None:
    """Recusa a Rodada se os parâmetros não estão congelados e commitados.

    `mudancas_nao_commitadas` é a saída de `git status --porcelain parametros.toml`
    (vazia quando o arquivo está igual ao último commit).
    """
    if not congelado:
        raise ParametrosNaoCongelados(
            "parametros.toml não está congelado (estado.congelado = false). Termine os ajustes com as "
            "Perguntas de desenvolvimento, mude para true e faça o commit antes da Rodada principal."
        )
    if mudancas_nao_commitadas.strip():
        raise ParametrosNaoCongelados(
            "parametros.toml tem mudança não commitada. Faça o commit antes da Rodada principal, "
            "para que o congelamento fique registrado no histórico."
        )


def status_git(arquivo: Path, raiz: Path) -> str:
    resultado = subprocess.run(
        ["git", "status", "--porcelain", "--", str(arquivo)],
        cwd=raiz, capture_output=True, text=True, check=True,
    )
    return resultado.stdout


def commit_atual(raiz: Path) -> str:
    resultado = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=raiz, capture_output=True, text=True, check=False
    )
    return resultado.stdout.strip() or "sem-commit"

# -*- coding: utf-8 -*-
"""Travas que impedem uma Rodada principal fora das regras do desenho.

POR QUE ISTO EXISTE. Duas regras do projeto só valem se forem verificadas por
código, e não por memória:

- ADR 0002: os parâmetros são congelados por commit antes da Rodada
  principal. Ajustá-los depois de ver os resultados sobre o Gabarito
  inflaria a taxa de acerto.
- A Revisão: nenhuma linha do Gabarito sem conferência do autor no PDF
  (essa trava está em gabarito.carregar_gabarito).

Cada Rodada guarda, no execucao.json ao lado das respostas, os parâmetros e
todos os commits em que rodou (ela é retomável), e uma Rodada publicada não
é retomada com parâmetros diferentes dos registrados.

As Rodadas de desenvolvimento não passam por estas travas e nunca entram nos
números publicados.
"""

from __future__ import annotations

import json
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


class ParametrosMudaram(RuntimeError):
    pass


def ler_commits(execucao: dict) -> list[str]:
    """Os commits em que a Rodada rodou, na ordem.

    O execucao.json antigo trazia só `commit`, sobrescrito a cada retomada: ele
    vale como uma lista de um.
    """
    if "commits" in execucao:
        return list(execucao["commits"])
    return [execucao["commit"]] if execucao.get("commit") else []


def registrar_execucao(pasta: Path, commit: str, parametros: dict, exigir_mesmos_parametros: bool = True) -> None:
    """Grava em pasta/execucao.json o commit desta execução e os parâmetros, sem apagar os anteriores.

    A Rodada é retomável e pode rodar em mais de um commit: cada um entra na
    lista `commits`, na ordem, uma vez só. Nas Rodadas publicadas
    (`exigir_mesmos_parametros`), retomar com parâmetros diferentes dos
    registrados é recusado antes de gravar qualquer coisa: uma Rodada com
    dois conjuntos de parâmetros não mede nenhum deles.
    """
    caminho = Path(pasta) / "execucao.json"
    anterior = json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}
    parametros = json.loads(json.dumps(parametros))  # tuplas viram listas, como ficam no JSON
    registrados = anterior.get("parametros")
    if exigir_mesmos_parametros and registrados and registrados != parametros:
        mudaram = sorted(k for k in {*registrados, *parametros} if registrados.get(k) != parametros.get(k))
        raise ParametrosMudaram(
            f"os parâmetros mudaram desde o início desta Rodada ({', '.join(mudaram)}; registrados em {caminho}). "
            "Volte o parametros.toml aos registrados para retomá-la, ou comece uma Rodada nova."
        )
    commits = ler_commits(anterior)
    if commit not in commits:
        commits.append(commit)
    novo = {k: v for k, v in anterior.items() if k != "commit"}
    novo.update(commits=commits, parametros=parametros)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(novo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

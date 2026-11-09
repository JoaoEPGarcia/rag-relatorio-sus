# -*- coding: utf-8 -*-
"""Confere a chave da API da Anthropic sem gastar: lista os modelos disponíveis.

POR QUE ISTO EXISTE. O wizard (scripts/configurar_maquina.sh) grava a chave no
.env e precisa saber se ela funciona antes de qualquer Rodada paga. Listar os
modelos não tem custo e confirma, de uma vez, que a chave é válida e que o
modelo dos parâmetros (claude-opus-5-5) está disponível para a conta.

Uso: uv run python scripts/conferir_chave.py  (lê ANTHROPIC_API_KEY do ambiente ou do .env)
"""

import sys

import anthropic

from rag_sus import config


def main() -> int:
    config.carregar_env()
    modelo = config.carregar_parametros().modelo_respondedor
    try:
        ids = [m.id for m in anthropic.Anthropic().models.list()]
    except anthropic.AuthenticationError:
        print("Chave inválida.")
        return 1
    except anthropic.APIError as erro:
        print(f"Falha ao consultar a API: {type(erro).__name__}")
        return 1
    if modelo not in ids:
        print(f"A chave funciona, mas o modelo {modelo} não aparece para esta conta.")
        return 1
    print(f"Chave válida; {modelo} disponível.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

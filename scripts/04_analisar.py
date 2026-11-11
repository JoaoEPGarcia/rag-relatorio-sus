# -*- coding: utf-8 -*-
"""Passo 4: da Rodada principal aos números publicados (não chama o modelo).

POR QUE ISTO EXISTE. É a casca de rag_sus.avaliacao.resultados.analisar: lê
as Rodadas em resultados/rodadas/ e a folha avaliacao/revisao_veredictos.csv,
grava todos os números no registro resultados/numeros.json e escreve as
linhas das tabelas do Relatório de avaliação em relatorio/tabelas/. Para se
alguma Condição da Rodada principal não respondeu todas as Perguntas do
Gabarito, ou se houver Veredicto do Juiz sem Revisão, e lista as Perguntas
que faltam ou estão pendentes.

Depois, rode scripts/06_gerar_documentos.py para levar os números ao
README, às macros LaTeX e ao NUMEROS_CANONICOS.md.

Uso:
  uv run python scripts/04_analisar.py
Sobre as Rodadas sintéticas (raiz temporária, nunca o registro real):
  RAG_SUS_RAIZ=/tmp/rag-sus-demo uv run python scripts/04_analisar.py
"""

import sys

from rag_sus import config
from rag_sus.avaliacao.gabarito import GabaritoInvalido
from rag_sus.avaliacao.resultados import RodadaIncompleta, RodadaSemParametros, analisar
from rag_sus.avaliacao.rodada import RevisaoIncompleta
from rag_sus.avaliacao.sinteticas import RaizProibida


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        registrados = analisar(config.RODADAS, config.REVISAO_VEREDICTOS)
    except (RevisaoIncompleta, RodadaIncompleta, FileNotFoundError, RaizProibida, RodadaSemParametros,
            GabaritoInvalido) as erro:
        print(f"Análise parada: {erro}")
        return 1
    print(f"{len(registrados)} números -> {config.NUMEROS}")
    print(f"Linhas das tabelas -> {config.TABELAS}")
    destaque = (registrados["ic_nivel"], registrados["destaque_acerto_com_rag"],
                registrados["destaque_acerto_com_rag_inf"], registrados["destaque_acerto_com_rag_sup"],
                registrados["destaque_acerto_sem_rag"])
    print("Acerto da resposta com RAG: {1} (IC {0}%: {2} a {3}), contra {4} sem RAG".format(*destaque))
    if registrados["repeticoes_condicoes_incompletas"] != "0":
        print(f"Repetição incompleta, fora da concordância até terminar: {registrados['repeticoes_incompletas']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

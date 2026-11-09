# -*- coding: utf-8 -*-
"""Grava Rodadas sintéticas de demonstração numa raiz temporária (não chama o modelo).

POR QUE ISTO EXISTE. Para conferir a análise, as figuras, o Relatório de
avaliação e o pipeline antes da Rodada principal, sem chave de API. Grava,
em <raiz>:
  resultados/rodadas/principal/{com_rag,sem_rag,contexto_completo}.jsonl
  resultados/rodadas/repeticaoN/... (uma pasta por repetição pedida)
  resultados/rodadas/*/execucao.json   (com "sintetica": true)
  avaliacao/revisao_veredictos.csv     (já revisada, com Veredictos mudados)

Os números são inventados. Por isso o script recusa uma raiz que seja (ou
esteja dentro de) uma cópia do projeto, e a análise recusa publicar Rodadas
sintéticas no registro de uma cópia do projeto. A mesma semente gera sempre
os mesmos arquivos; rodar de novo na mesma raiz substitui as Rodadas.

Uso (Git Bash; a raiz vem de --raiz ou de RAG_SUS_RAIZ):
  export RAG_SUS_RAIZ="$(mktemp -d)"
  uv run python scripts/gerar_rodadas_sinteticas.py [--semente 2026] [--repeticoes 2]
  uv run python scripts/04_analisar.py           # registro e tabelas em $RAG_SUS_RAIZ
  uv run python scripts/06_gerar_documentos.py   # precisa de README.base.md em $RAG_SUS_RAIZ
"""

import argparse
import os
import sys
from pathlib import Path

from rag_sus.avaliacao.sinteticas import RaizProibida, gerar_rodadas_sinteticas


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Rodadas sintéticas de demonstração numa raiz temporária.")
    ap.add_argument("--raiz", default=os.environ.get("RAG_SUS_RAIZ"),
                    help="raiz temporária (padrão: a variável RAG_SUS_RAIZ)")
    ap.add_argument("--semente", type=int, default=2026)
    ap.add_argument("--repeticoes", type=int, default=2, choices=(0, 1, 2))
    args = ap.parse_args()
    if not args.raiz:
        print("Diga a raiz temporária com --raiz ou com a variável RAG_SUS_RAIZ.")
        return 2
    try:
        pasta = gerar_rodadas_sinteticas(Path(args.raiz), semente=args.semente, repeticoes=args.repeticoes)
    except RaizProibida as erro:
        print(f"Recusado: {erro}")
        return 1
    print(f"Rodadas sintéticas (semente {args.semente}, {args.repeticoes} repetição(ões)) -> {pasta}")
    print(f"Para analisar: RAG_SUS_RAIZ={Path(args.raiz)} uv run python scripts/04_analisar.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

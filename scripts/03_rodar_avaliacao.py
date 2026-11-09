# -*- coding: utf-8 -*-
"""Passo 3: roda uma Rodada de avaliação (chama o Gemini, gasta cota ou créditos).

POR QUE ISTO EXISTE. Passa as Perguntas por cada Condição e grava uma linha
por Pergunta em resultados/rodadas/<rodada>/<condicao>.jsonl. A Rodada é
retomável: rodar de novo continua de onde parou. Se a cota diária acabar, ou
o saldo pré-pago (créditos do Google AI Pro) zerar no meio, o script para e
avisa; o mesmo comando continua dali quando a cota renovar (ADR 0005).

- desenvolvimento: Perguntas de desenvolvimento, sem travas, nunca publicada.
- principal: o Gabarito revisado, com os parâmetros congelados (ADR 0002).
  Ao fim, grava a folha de Revisão dos Veredictos do Juiz em
  avaliacao/revisao_veredictos.csv, que o autor preenche.
- repeticao1, repeticao2: mesmas travas; só medem a concordância entre Rodadas.

Sem --confirmar, o script só mostra quantas chamadas faria e para.

Uso:
  uv run python scripts/03_rodar_avaliacao.py --rodada desenvolvimento --confirmar
  uv run python scripts/03_rodar_avaliacao.py --rodada principal --confirmar
"""

import argparse
import json
import os
import sys

from rag_sus import config
from rag_sus.assistente import CONDICOES, Assistente
from rag_sus.avaliacao.gabarito import carregar_gabarito
from rag_sus.avaliacao.juiz import Juiz
from rag_sus.avaliacao.rodada import executar_rodada, gravar_folha_de_revisao
from rag_sus.avaliacao.travas import RODADAS, commit_atual, status_git, verificar_congelamento
from rag_sus.busca import E5Embutidor, IndiceDeTrechos
from rag_sus.provedores import CotaDiariaEsgotada, CotaEsgotada, provedor_do_ambiente

FOLHA = config.AVALIACAO / "revisao_veredictos.csv"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rodada", choices=RODADAS, required=True)
    ap.add_argument("--condicoes", default=",".join(CONDICOES))
    ap.add_argument("--limite", type=int, default=None, help="só as N primeiras Perguntas (teste rápido)")
    ap.add_argument("--confirmar", action="store_true", help="sem isto, só mostra o que faria")
    args = ap.parse_args()

    config.carregar_env()
    p = config.carregar_parametros()
    condicoes = [c.strip() for c in args.condicoes.split(",") if c.strip()]

    if args.rodada == "desenvolvimento":
        itens = carregar_gabarito(config.PERGUNTAS_DESENVOLVIMENTO, exigir_revisao=False)
    else:
        verificar_congelamento(p.congelado, status_git(config.PARAMETROS, config.RAIZ))
        itens = carregar_gabarito(config.GABARITO, exigir_revisao=True)
    if args.limite:
        itens = itens[: args.limite]

    pasta = config.RESULTADOS / "rodadas" / args.rodada
    print(f"Rodada {args.rodada}: {len(itens)} Perguntas x {len(condicoes)} Condições "
          f"= até {len(itens) * len(condicoes)} chamadas ao respondedor ({p.modelo_respondedor}), "
          f"mais as do Juiz. Retoma o que já está em {pasta}.")
    if os.environ.get("PROVEDOR", "gemini") == "gemini":
        plano = os.environ.get("GEMINI_PLANO", "gratuito")
        print(f"Plano do Gemini: {plano}"
              + (" (gasta os créditos do Google AI Pro; o teto é o saldo pré-pago)."
                 if plano == "creditos-ai-pro" else " (sem custo; para se a cota diária acabar)."))
    if not args.confirmar:
        print("Nada foi chamado. Rode de novo com --confirmar para executar.")
        return 0

    embutidor = E5Embutidor(pasta_cache=config.CACHE_MODELOS)
    indice = IndiceDeTrechos.carregar(config.INDICE, embutidor)
    texto = config.TEXTO_COMPLETO.read_text(encoding="utf-8")
    respondedor = provedor_do_ambiente(p.modelo_respondedor, p.esforco_respondedor, p.max_tokens_respondedor)
    juiz = Juiz(provedor_do_ambiente(p.modelo_juiz, p.esforco_juiz, p.max_tokens_juiz))
    assistente = Assistente(respondedor, indice, embutidor, k=p.k, texto_completo=texto)

    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "execucao.json").write_text(
        json.dumps({"commit": commit_atual(config.RAIZ), "parametros": p.__dict__}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    def progresso(linha: dict) -> None:
        marca = {True: "certo", False: "errado", None: "juiz"}[linha["acerto_regra"]]
        print(f"  {linha['condicao']:18} {linha['id']:5} {marca:6} {linha['tokens_entrada']:>7} tokens")

    rodadas = []
    for condicao in condicoes:
        destino = pasta / f"{condicao}.jsonl"
        print(f"Condição {condicao} -> {destino}")
        try:
            executar_rodada(itens, condicao, assistente, juiz, destino, ao_responder=progresso)
        except CotaEsgotada as erro:
            print(f"Parado: {erro}.")
            quando = "amanhã" if isinstance(erro, CotaDiariaEsgotada) else "quando houver saldo"
            print(f"O que já foi respondido está salvo. Rode o mesmo comando {quando} para continuar.")
            return 3
        rodadas.append(destino)

    if args.rodada == "principal":
        n = gravar_folha_de_revisao(rodadas, FOLHA)
        print(f"{n} Veredicto(s) do Juiz para revisar em {FOLHA} (coluna veredicto_revisado: certo/errado).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

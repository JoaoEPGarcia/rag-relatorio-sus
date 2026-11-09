# -*- coding: utf-8 -*-
"""Análise das Rodadas consolidadas: taxas, comparações pareadas e erros.

POR QUE ISTO EXISTE. Depois de `consolidar`, cada linha tem o Veredicto final
de uma Pergunta numa Condição. Aqui saem os números do resultado: as três
medidas com intervalo de Wilson, a comparação pareada entre Condições
(McNemar exato e intervalo de Newcombe), as Classes de erro cruzadas com o
Tipo de pergunta, e a concordância entre Rodadas. Perguntas respondíveis e
sem resposta são sempre contadas em separado (docs/DESENHO.md).
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

from rag_sus.avaliacao.estatistica import diferenca_pareada, mcnemar_exato, tabela_pareada, wilson


def _wilson_de(valores: list[bool]):
    return wilson(sum(valores), len(valores)) if valores else None


def resumir(linhas: list[dict]) -> dict:
    respondiveis = [l for l in linhas if l["respondivel"]]
    sem_resposta = [l for l in linhas if not l["respondivel"]]
    recuperacao = [l["acerto_recuperacao"] for l in respondiveis if l["acerto_recuperacao"] is not None]
    custos = [(l["custo_usd"] or 0.0) for l in linhas if l["custo_usd"] is not None]
    latencias = [l["latencia_s"] for l in linhas if l["latencia_s"] is not None]
    tokens = [l["tokens_entrada"] for l in linhas if l.get("tokens_entrada") is not None]
    return {
        "n_respondiveis": len(respondiveis),
        "n_sem_resposta": len(sem_resposta),
        "acertos_resposta": sum(l["acerto_resposta"] for l in respondiveis),
        "acerto_resposta": _wilson_de([l["acerto_resposta"] for l in respondiveis]),
        "acerto_citacao": _wilson_de([bool(l["acerto_citacao"]) for l in respondiveis]),
        "acerto_recuperacao": _wilson_de(recuperacao) if recuperacao else None,
        "abstencao_correta": _wilson_de([l["acerto_resposta"] for l in sem_resposta]),
        "erros": dict(Counter(l["classe_erro"] for l in linhas if l["classe_erro"])),
        "custo_medio_usd": statistics.fmean(custos) if custos else None,
        # Sem fatura no plano gratuito, o custo de cada Condição é medido em tokens de entrada.
        "tokens_entrada_medio": statistics.fmean(tokens) if tokens else None,
        "latencia_mediana_s": statistics.median(latencias) if latencias else None,
        "n_fallback": sum(bool(l.get("usou_fallback")) for l in linhas),
    }


def comparar(linhas_a: list[dict], linhas_b: list[dict]) -> dict:
    """Comparação pareada do Acerto da resposta nas Perguntas respondíveis."""
    a = {l["id"]: l["acerto_resposta"] for l in linhas_a if l["respondivel"]}
    b = {l["id"]: l["acerto_resposta"] for l in linhas_b if l["respondivel"]}
    if set(a) != set(b):
        raise ValueError("as duas Condições precisam ter as mesmas Perguntas respondíveis")
    ids = sorted(a)
    t = tabela_pareada([a[i] for i in ids], [b[i] for i in ids])
    return {
        "tabela": t,
        "diferenca": diferenca_pareada(t.ambos, t.so_a, t.so_b, t.nenhum),
        "p_mcnemar": mcnemar_exato(t.so_a, t.so_b),
    }


def erros_por_tipo(linhas: list[dict]) -> dict[str, dict[str, int]]:
    """Para cada Tipo de pergunta: quantas há (n) e quantas caem em cada Classe de erro."""
    saida: dict[str, dict[str, int]] = defaultdict(dict)
    for l in linhas:
        if not l["respondivel"]:
            continue
        celula = saida[l["tipo"]]
        celula["n"] = celula.get("n", 0) + 1
        if l["classe_erro"]:
            celula[l["classe_erro"]] = celula.get(l["classe_erro"], 0) + 1
    return dict(saida)


def _veredicto_automatico(l: dict) -> bool:
    """Veredicto antes da Revisão: o do Juiz, se houve; senão, o da regra."""
    return bool(l["veredicto_juiz"]) if l["veredicto_juiz"] is not None else bool(l["acerto_regra"])


def concordancia(principal: list[dict], repeticao: list[dict]) -> float:
    """Fração das Perguntas em que duas Rodadas dão o mesmo Veredicto automático."""
    a = {l["id"]: _veredicto_automatico(l) for l in principal}
    b = {l["id"]: _veredicto_automatico(l) for l in repeticao}
    comuns = sorted(set(a) & set(b))
    if not comuns:
        raise ValueError("as Rodadas não têm Perguntas em comum")
    return sum(a[i] == b[i] for i in comuns) / len(comuns)

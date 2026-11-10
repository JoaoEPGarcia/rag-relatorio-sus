# -*- coding: utf-8 -*-
"""Execução de uma Rodada, folha de Revisão dos Veredictos e consolidação.

POR QUE ISTO EXISTE. Uma Rodada passa todas as Perguntas do Gabarito por uma
Condição e grava uma linha por Pergunta (JSONL), com a resposta, as páginas,
as medidas e o custo. Três cuidados:

- é retomável: uma Pergunta já gravada não é perguntada de novo, então uma
  queda de rede no meio não custa a Rodada inteira;
- o Juiz só é chamado quando a regra não basta (respostas descritivas, e
  numéricas que a regra reprovou, para pegar falso negativo da regra);
- os Veredictos do Juiz vão para uma folha de Revisão (CSV) que o autor
  preenche com "certo" ou "errado". Na Rodada principal, `consolidar` recusa
  produzir resultado enquanto houver Veredicto do Juiz sem Revisão, e a
  Revisão do autor vence o Juiz.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from rag_sus.avaliacao.gabarito import ItemGabarito
from rag_sus.avaliacao.pontuacao import (
    acerto_citacao,
    acerto_numerico,
    acerto_recuperacao,
    classificar_erro,
)

COLUNAS_FOLHA = (
    "condicao", "id", "pergunta", "gabarito", "resposta",
    "veredicto_juiz", "justificativa_juiz", "veredicto_revisado", "comentario",
)
VALORES_REVISAO = {"certo": True, "errado": False}


class RevisaoIncompleta(ValueError):
    pass


def carregar_linhas(caminho: Path) -> list[dict]:
    if not Path(caminho).exists():
        return []
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def executar_rodada(itens: list[ItemGabarito], condicao: str, assistente, juiz, destino: Path,
                    ao_responder=None) -> list[dict]:
    """Responde cada Pergunta ainda não gravada em `destino` e grava a linha."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    feitas = {l["id"] for l in carregar_linhas(destino)}

    for item in itens:
        if item.id in feitas:
            continue
        linha = _responder_e_pontuar(item, condicao, assistente, juiz)
        with open(destino, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        if ao_responder:
            ao_responder(linha)
    return carregar_linhas(destino)


def _responder_e_pontuar(item: ItemGabarito, condicao: str, assistente, juiz) -> dict:
    r = assistente.responder(item.pergunta, condicao)

    if not item.respondivel:
        acerto_regra: bool | None = r.abstencao
    elif r.abstencao:
        acerto_regra = False
    elif item.numerico:
        acerto_regra = acerto_numerico(r.resposta, item.valores)
    else:
        acerto_regra = None

    precisa_do_juiz = item.respondivel and not r.abstencao and acerto_regra is not True
    veredicto = juiz.julgar(item.pergunta, item.resposta, r.resposta) if precisa_do_juiz else None

    meta = r.metadados
    meta_juiz = veredicto.metadados if veredicto else None
    return {
        "id": item.id,
        "tipo": item.tipo,
        "respondivel": item.respondivel,
        "condicao": condicao,
        "pergunta": item.pergunta,
        "gabarito": item.resposta,
        "paginas_gabarito": list(item.paginas),
        "resposta": r.resposta,
        "paginas_citadas": list(r.paginas_citadas),
        "abstencao": r.abstencao,
        "paginas_recuperadas": list(r.paginas_recuperadas),
        "trechos_recuperados": list(r.trechos_recuperados),
        "acerto_regra": acerto_regra,
        "veredicto_juiz": veredicto.acerto if veredicto else None,
        "justificativa_juiz": veredicto.justificativa if veredicto else "",
        "modelo_juiz": meta_juiz.modelo_que_respondeu if meta_juiz else "",
        "acerto_citacao": acerto_citacao(r.paginas_citadas, item.paginas) if item.respondivel else None,
        "acerto_recuperacao": (
            acerto_recuperacao(r.paginas_recuperadas, item.paginas)
            if condicao == "com_rag" and item.respondivel
            else None
        ),
        "modelo_que_respondeu": meta.modelo_que_respondeu if meta else "",
        "usou_fallback": meta.usou_fallback if meta else False,
        "tokens_entrada": meta.tokens_entrada if meta else 0,
        "tokens_saida": meta.tokens_saida if meta else 0,
        "tokens_cache_escrita": meta.tokens_cache_escrita if meta else 0,
        "tokens_cache_leitura": meta.tokens_cache_leitura if meta else 0,
        "custo_usd": meta.custo_usd if meta else None,
        "custo_juiz_usd": meta_juiz.custo_usd if meta_juiz else 0.0,
        "latencia_s": meta.latencia_s if meta else None,
        "id_requisicao": meta.id_requisicao if meta else "",
    }


def gravar_folha_de_revisao(rodadas: list[Path], folha: Path) -> int:
    """Grava a folha com os Veredictos do Juiz, preservando o que já foi revisado."""
    folha = Path(folha)
    ja_revisado: dict[tuple[str, str], dict] = {}
    if folha.exists():
        with open(folha, encoding="utf-8", newline="") as f:
            for l in csv.DictReader(f):
                ja_revisado[(l["condicao"], l["id"])] = l

    saida = []
    for caminho in rodadas:
        for l in carregar_linhas(caminho):
            if l["veredicto_juiz"] is None:
                continue
            anterior = ja_revisado.get((l["condicao"], l["id"]), {})
            saida.append({
                "condicao": l["condicao"],
                "id": l["id"],
                "pergunta": l["pergunta"],
                "gabarito": l["gabarito"],
                "resposta": l["resposta"],
                "veredicto_juiz": "certo" if l["veredicto_juiz"] else "errado",
                "justificativa_juiz": l["justificativa_juiz"],
                "veredicto_revisado": anterior.get("veredicto_revisado", ""),
                "comentario": anterior.get("comentario", ""),
            })

    folha.parent.mkdir(parents=True, exist_ok=True)
    with open(folha, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS_FOLHA, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(saida)
    return len(saida)


def consolidar(rodada: Path, folha: Path | None, exigir_revisao: bool) -> list[dict]:
    """Veredicto final de cada Pergunta: regra, ou Juiz, ou a Revisão do autor."""
    revisados: dict[tuple[str, str], bool] = {}
    if folha and Path(folha).exists():
        with open(folha, encoding="utf-8", newline="") as f:
            for l in csv.DictReader(f):
                valor = l["veredicto_revisado"].strip().lower()
                if not valor:
                    continue
                if valor not in VALORES_REVISAO:
                    raise ValueError(f"{l['id']}: veredicto_revisado '{valor}' deve ser certo ou errado")
                revisados[(l["condicao"], l["id"])] = VALORES_REVISAO[valor]

    finais, faltando = [], []
    for l in carregar_linhas(rodada):
        l = dict(l)
        chave = (l["condicao"], l["id"])
        if l["veredicto_juiz"] is not None:
            if chave in revisados:
                l["acerto_resposta"] = revisados[chave]
                l["revisado_pelo_autor"] = True
            else:
                faltando.append(l["id"])
                l["acerto_resposta"] = l["veredicto_juiz"]
                l["revisado_pelo_autor"] = False
        else:
            l["acerto_resposta"] = bool(l["acerto_regra"])
            l["revisado_pelo_autor"] = False
        l["classe_erro"] = classificar_erro(
            l["acerto_resposta"],
            l["abstencao"],
            bool(l["acerto_citacao"]),
            l["acerto_recuperacao"],
            l["respondivel"],
        )
        finais.append(l)

    if exigir_revisao and faltando:
        raise RevisaoIncompleta(
            f"{len(faltando)} Veredicto(s) do Juiz sem Revisão em {Path(rodada).name}: {', '.join(faltando)}"
        )
    return finais

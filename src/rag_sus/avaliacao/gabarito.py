# -*- coding: utf-8 -*-
"""Carregamento e validação do Gabarito, com a trava da Revisão.

POR QUE ISTO EXISTE. A regra do projeto é que nenhum Gabarito entra na
avaliação sem a Revisão do autor, feita no PDF. Eu (o assistente que escreveu
este código) proponho as linhas com a coluna `revisado` vazia; só o autor a
preenche. Esta trava transforma o combinado em código: `carregar_gabarito`
recusa o arquivo inteiro se uma linha que seja estiver sem Revisão, e diz
quais. `exigir_revisao=False` existe só para mostrar a proposta ao autor.

Formato do CSV (UTF-8, vírgula como separador):
    id, pergunta, tipo, resposta, valores, paginas, revisado, observacao
- tipo: numero_prosa | numero_tabela | numero_legenda | conceito | sintese | sem_resposta
- valores: números que a resposta precisa conter, separados por ";", no
  formato brasileiro ("4,3;4,45"). Obrigatório nos tipos numéricos.
- paginas: páginas impressas, separadas por ";". Vazio só em sem_resposta.
- revisado: iniciais e data de quem conferiu no PDF. Vazio = não revisado.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from rag_sus.avaliacao.pontuacao import extrair_numeros

TIPOS_RESPONDIVEIS = ("numero_prosa", "numero_tabela", "numero_legenda", "conceito", "sintese")
TIPOS = (*TIPOS_RESPONDIVEIS, "sem_resposta")
COLUNAS = ("id", "pergunta", "tipo", "resposta", "valores", "paginas", "revisado", "observacao")


class GabaritoInvalido(ValueError):
    pass


class GabaritoNaoRevisado(ValueError):
    pass


@dataclass(frozen=True)
class ItemGabarito:
    id: str
    pergunta: str
    tipo: str
    resposta: str
    valores: tuple[float, ...]
    paginas: tuple[int, ...]
    revisado: str
    observacao: str = ""

    @property
    def respondivel(self) -> bool:
        return self.tipo != "sem_resposta"

    @property
    def numerico(self) -> bool:
        return self.tipo.startswith("numero_")


def carregar_gabarito(caminho: str | Path, exigir_revisao: bool = True) -> list[ItemGabarito]:
    with open(caminho, encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        faltando = set(COLUNAS) - set(leitor.fieldnames or [])
        if faltando:
            raise GabaritoInvalido(f"colunas ausentes no Gabarito: {sorted(faltando)}")
        itens = [_item(linha) for linha in leitor]

    vistos: set[str] = set()
    for item in itens:
        if item.id in vistos:
            raise GabaritoInvalido(f"id repetido no Gabarito: {item.id}")
        vistos.add(item.id)

    if exigir_revisao:
        sem_revisao = [i.id for i in itens if not i.revisado]
        if sem_revisao:
            raise GabaritoNaoRevisado(
                f"{len(sem_revisao)} linha(s) do Gabarito sem Revisão: {', '.join(sem_revisao)}. "
                "Confira cada uma no PDF e preencha a coluna 'revisado'."
            )
    return itens


def _item(linha: dict) -> ItemGabarito:
    id_ = (linha["id"] or "").strip()
    tipo = (linha["tipo"] or "").strip()
    if tipo not in TIPOS:
        raise GabaritoInvalido(f"{id_}: tipo '{tipo}' inválido; use um de {TIPOS}")

    paginas = tuple(int(p) for p in _partes(linha["paginas"]))
    valores = tuple(_um_numero(id_, v) for v in _partes(linha["valores"]))

    if tipo == "sem_resposta" and paginas:
        raise GabaritoInvalido(f"{id_}: Pergunta sem resposta não pode ter página")
    if tipo != "sem_resposta" and not paginas:
        raise GabaritoInvalido(f"{id_}: Pergunta respondível precisa de página")
    if tipo.startswith("numero_") and not valores:
        raise GabaritoInvalido(f"{id_}: tipo numérico precisa da coluna valores")
    if tipo == "sintese" and len(set(paginas)) < 2:
        raise GabaritoInvalido(f"{id_}: síntese entre páginas precisa de pelo menos duas páginas")

    return ItemGabarito(
        id=id_,
        pergunta=(linha["pergunta"] or "").strip(),
        tipo=tipo,
        resposta=(linha["resposta"] or "").strip(),
        valores=valores,
        paginas=paginas,
        revisado=(linha["revisado"] or "").strip(),
        observacao=(linha["observacao"] or "").strip(),
    )


def _partes(celula: str | None) -> list[str]:
    return [p.strip() for p in (celula or "").split(";") if p.strip()]


def _um_numero(id_: str, texto: str) -> float:
    numeros = extrair_numeros(texto)
    if len(numeros) != 1:
        raise GabaritoInvalido(f"{id_}: valor '{texto}' não é um número único")
    return numeros[0]

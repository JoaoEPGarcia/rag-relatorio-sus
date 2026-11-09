# -*- coding: utf-8 -*-
"""Tipos que atravessam o pipeline: o que sai da extração e o que entra na busca.

POR QUE ISTO EXISTE. A extração, a quebra, a busca e a avaliação trocam os
mesmos objetos. Defini-los num lugar só evita que cada módulo invente o seu
dicionário com chaves ligeiramente diferentes ("pagina", "page", "pag").
Os nomes seguem o GLOSSARY.md: Página é a impressa; a posição no arquivo é
a página do PDF.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

TipoBloco = Literal["paragrafo", "legenda", "tabela"]
TipoTrecho = Literal["texto", "legenda", "tabela"]


@dataclass(frozen=True)
class Bloco:
    """Unidade de conteúdo de uma página, já classificada pela extração.

    `texto` de uma tabela já vem serializado linha a linha. `secao` é o título
    da seção em vigor quando o bloco aparece (pode vir de uma página anterior).
    """

    tipo: TipoBloco
    texto: str
    secao: str = ""


@dataclass(frozen=True)
class Pagina:
    """Uma página do Relatório-fonte com os blocos na ordem de leitura."""

    pagina_pdf: int
    pagina_impressa: int
    blocos: tuple[Bloco, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Trecho:
    """O que se indexa e se recupera. Nunca atravessa a fronteira de página."""

    id: str
    texto: str
    pagina_impressa: int
    pagina_pdf: int
    tipo: TipoTrecho
    secao: str = ""

    def para_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def de_dict(cls, d: dict) -> Trecho:
        return cls(**d)

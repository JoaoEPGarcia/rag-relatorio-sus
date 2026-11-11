# -*- coding: utf-8 -*-
"""Conferência do PDF compilado: nada vaza a medida da figura, e nenhuma linha estoura.

POR QUE ISTO EXISTE. Na leitura das páginas do Relatório de avaliação, as
Tabelas 1 e 2 vazavam cerca de 0,7 cm de cada lado e só o olho pegou: a
`tabelaplena` do kit põe a tabela num \\makebox, e o pdflatex não acusa
Overfull. Esta conferência mede o PDF de verdade. A medida larga do kit é o
papel menos 1 cm de cada lado (`\\figwidth`); nenhum caractere pode passar
dela. E o .log não pode ter Overfull acima de 1 pt (os menores não se veem).
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

MARGEM_PT = 72 / 2.54  # 1 cm: a margem do papel que o \figwidth do kit deixa de cada lado
_OVERFULL = re.compile(r"Overfull \\hbox \(([\d.]+)pt too wide\)[^\n]*?lines (\d+--\d+)")


def fora_da_margem(pdf: Path, margem_pt: float = MARGEM_PT, folga_pt: float = 1.0) -> list[tuple[int, str]]:
    """Cada linha com texto além da margem: a página e a linha inteira (até 60 caracteres)."""
    achados = []
    with pdfplumber.open(pdf) as doc:
        for numero, pagina in enumerate(doc.pages, start=1):
            limite_esq, limite_dir = margem_pt - folga_pt, pagina.width - margem_pt + folga_pt
            alturas = sorted({round(c["top"]) for c in pagina.chars if c["x0"] < limite_esq or c["x1"] > limite_dir})
            for altura in alturas:
                linha = sorted((c for c in pagina.chars if abs(c["top"] - altura) <= 1), key=lambda c: c["x0"])
                achados.append((numero, "".join(c["text"] for c in linha)[:60]))
    return achados


def overfull(log: str, limite_pt: float = 1.0) -> list[str]:
    """Os Overfull \\hbox do .log acima do limite, com as linhas do .tex."""
    return [f"{float(pt):.1f}pt nas linhas {linhas}" for pt, linhas in _OVERFULL.findall(log)
            if float(pt) > limite_pt]

# -*- coding: utf-8 -*-
"""Testes da conferência do PDF: texto fora da medida da figura e Overfull no .log."""

import pytest

from rag_sus.conferencia_pdf import MARGEM_PT, fora_da_margem, overfull

matplotlib = pytest.importorskip("matplotlib")


def pdf_com_textos(caminho, posicoes_pt):
    """Uma página A4 com uma palavra em cada x (em pt), fonte TrueType para o texto ser extraível."""
    from matplotlib.figure import Figure  # sem pyplot: nenhum backend de janela

    with matplotlib.rc_context({"pdf.fonttype": 42}):
        largura, altura = 595.28, 841.89
        fig = Figure(figsize=(largura / 72, altura / 72))
        for i, x in enumerate(posicoes_pt):
            fig.text(x / largura, 0.9 - i * 0.05, f"palavra{i}", fontsize=10, ha="left")
        fig.savefig(caminho)
    return caminho


def test_texto_dentro_da_medida_passa(tmp_path):
    pdf = pdf_com_textos(tmp_path / "ok.pdf", [MARGEM_PT + 10, 300])

    assert fora_da_margem(pdf) == []


def test_texto_que_vaza_a_margem_e_listado_com_a_pagina(tmp_path):
    # a Tabela 1 vazava cerca de 0,7 cm de cada lado: começava antes do 1 cm de margem do papel
    pdf = pdf_com_textos(tmp_path / "vaza.pdf", [MARGEM_PT + 10, 8])

    achados = fora_da_margem(pdf)

    assert len(achados) == 1
    pagina, texto = achados[0]
    assert pagina == 1 and "palavra1" in texto


def test_overfull_acima_do_limite_e_listado_e_o_pequeno_nao():
    log = (
        "Overfull \\hbox (13.59573pt too wide) in paragraph at lines 800--807\n"
        "Overfull \\hbox (0.22067pt too wide) in paragraph at lines 809--812\n"
        "Underfull \\hbox (badness 10000) in paragraph at lines 1--2\n"
    )

    assert overfull(log) == ["13.6pt nas linhas 800--807"]

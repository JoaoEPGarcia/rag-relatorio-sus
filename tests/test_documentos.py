# -*- coding: utf-8 -*-
"""Testes da geração dos documentos a partir do registro de números (ADR 0003)."""

import pytest

from rag_sus.documentos import (
    MarcadorDesconhecido,
    digitos_soltos_no_markdown,
    digitos_soltos_no_tex,
    gerar_numeros_canonicos,
    gerar_numeros_tex,
    nome_macro,
    preencher_readme,
    texto_tex,
    usos,
)

REGISTRO = {
    "acerto_com_rag": {"valor": 0.8, "texto": "80,0%", "descricao": "acerto com RAG",
                       "script": "scripts/04_analisar.py", "formato": "pct1"},
    "corpus_trechos": {"valor": 570, "texto": "570", "descricao": "Trechos indexados",
                       "script": "scripts/01_extrair.py", "formato": "inteiro"},
    "dif_repeticao1": {"valor": -0.05, "texto": "−5,0 p.p.", "descricao": "diferença",
                       "script": "scripts/04_analisar.py", "formato": "pp1",
                       "aparece_em": ["figuras/acerto.png (título)"]},
}


def test_nome_macro_vira_camelcase_sem_digitos():
    assert nome_macro("acerto_com_rag") == "NumAcertoComRag"
    assert nome_macro("dif_repeticao1") == "NumDifRepeticaoUm"
    assert nome_macro("k") == "NumK"


@pytest.mark.parametrize(
    "texto,esperado",
    [("80,0%", r"80,0\%"), ("−5,0 p.p.", "$-$5,0 p.p."), ("US$ 2,50", r"US\$ 2,50"),
     ("< 0,001", "$<$ 0,001"), ("1.236", "1.236")],
)
def test_texto_tex_escapa_o_que_o_pdflatex_nao_aceita(texto, esperado):
    assert texto_tex(texto) == esperado


def test_gerar_numeros_tex():
    tex = gerar_numeros_tex(REGISTRO)

    assert tex.startswith("% GERADO por scripts/06_gerar_documentos.py")
    assert r"\newcommand{\NumAcertoComRag}{80,0\%}" in tex
    assert r"\newcommand{\NumCorpusTrechos}{570}" in tex


def test_preencher_readme_troca_os_marcadores():
    base = "O assistente acerta {{acerto_com_rag}} sobre {{corpus_trechos}} Trechos."
    assert preencher_readme(base, REGISTRO) == "O assistente acerta 80,0% sobre 570 Trechos."


def test_marcador_desconhecido_e_erro():
    with pytest.raises(MarcadorDesconhecido, match="acerto_inventado"):
        preencher_readme("{{acerto_inventado}}", REGISTRO)


def test_usos_encontra_readme_relatorio_e_figuras():
    tex = {"relatorio/relatorio.tex": r"são \NumCorpusTrechos{} e \NumAcertoComRag"}
    u = usos(REGISTRO, "acerta {{acerto_com_rag}}", tex)

    assert u["acerto_com_rag"] == ["README", "relatorio/relatorio.tex"]
    assert u["corpus_trechos"] == ["relatorio/relatorio.tex"]
    assert u["dif_repeticao1"] == ["figuras/acerto.png (título)"]


def test_macro_que_e_prefixo_de_outra_nao_conta_como_uso():
    registro = {"k": {"texto": "6", "descricao": "", "script": "s", "valor": 6, "formato": "inteiro"},
                "k_maximo": {"texto": "9", "descricao": "", "script": "s", "valor": 9, "formato": "inteiro"}}
    u = usos(registro, "", {"r.tex": r"\NumKMaximo"})
    assert u["k"] == [] and u["k_maximo"] == ["r.tex"]


def test_gerar_numeros_canonicos_tem_as_colunas_do_kit():
    md = gerar_numeros_canonicos(REGISTRO, usos(REGISTRO, "{{acerto_com_rag}}", {}))

    assert "| Número | Valor | O que é | Sai de | Onde aparece |" in md
    assert r"| `\NumAcertoComRag` | 80,0% | acerto com RAG | `scripts/04_analisar.py` | README |" in md
    assert "(não impresso)" in md  # corpus_trechos não aparece em lugar nenhum


def test_digitos_soltos_no_markdown_ignora_codigo_links_e_marcadores():
    texto = (
        "Acerta {{acerto_com_rag}}. Rode `scripts/01_extrair.py` e veja [ADR](docs/adr/0002-x.md).\n"
        "```\nuv run python scripts/03_rodar_avaliacao.py\n```\n"
        "Mas aqui há 42 hospitais digitados."
    )
    assert digitos_soltos_no_markdown(texto) == ["42"]


def test_marcador_de_lista_numerada_nao_e_numero_digitado():
    texto = "1. **Extração.** Texto.\n   2. subitem\n10. décimo passo, com 7 erros."
    assert digitos_soltos_no_markdown(texto) == ["7"]


def test_digitos_soltos_no_tex_ignora_comandos_opcoes_e_comentarios():
    tex = (
        "\\documentclass{article}\n\\begin{document}\n"
        "\\section{Resultados}\n\\imagemplena[0.86]{acerto_rag}\n"
        "O acerto foi \\NumAcertoComRag{} % comentário com 99\n"
        "\\vspace{2mm} contra 37 digitados.\n\\end{document}\n"
    )
    assert digitos_soltos_no_tex(tex) == ["37"]

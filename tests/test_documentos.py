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
    textos_do_relatorio,
    usos,
)

REGISTRO = {
    "acerto_com_rag": {"valor": 0.8, "texto": "80,0%", "texto_en": "80.0%", "descricao": "acerto com RAG",
                       "script": "scripts/04_analisar.py", "formato": "pct1"},
    "corpus_trechos": {"valor": 570, "texto": "570", "texto_en": "570", "descricao": "Trechos indexados",
                       "script": "scripts/01_extrair.py", "formato": "inteiro"},
    "dif_repeticao1": {"valor": -0.05, "texto": "−5,0 p.p.", "texto_en": "−5.0 pp", "descricao": "diferença",
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


def test_marcador_en_usa_o_texto_em_ingles():
    base = "Com RAG: {{acerto_com_rag}}, {{dif_repeticao1}}. With RAG: {{acerto_com_rag:en}}, {{ dif_repeticao1:en }}."
    assert preencher_readme(base, REGISTRO) == "Com RAG: 80,0%, −5,0 p.p.. With RAG: 80.0%, −5.0 pp."


def test_marcador_desconhecido_e_erro_e_lista_todos_os_que_faltam():
    with pytest.raises(MarcadorDesconhecido, match="acerto_inventado.*outro_inventado"):
        preencher_readme("{{acerto_inventado}} e {{outro_inventado:en}} e {{acerto_com_rag}}", REGISTRO)


def test_marcador_en_sem_texto_em_ingles_no_registro_e_erro():
    antigo = {"n": {"valor": 1236, "texto": "1.236", "descricao": "", "script": "scripts/01_extrair.py",
                    "formato": "inteiro"}}
    with pytest.raises(MarcadorDesconhecido, match="inglês.*scripts/01_extrair.py"):
        preencher_readme("{{n:en}}", antigo)


def test_marcador_en_conta_como_uso_e_nao_como_numero_digitado():
    assert usos(REGISTRO, "In English: {{corpus_trechos:en}}", {})["corpus_trechos"] == ["README"]
    assert digitos_soltos_no_markdown("Main findings: {{acerto_com_rag:en}} with RAG.") == []


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


def test_textos_conferidos_deixam_de_fora_o_que_o_script_gera(tmp_path):
    relatorio = tmp_path / "relatorio"
    (relatorio / "tabelas").mkdir(parents=True)
    (relatorio / "secoes").mkdir()
    (relatorio / "relatorio.tex").write_text("\\NumAcertoComRag", encoding="utf-8")
    (relatorio / "secoes" / "resultados.tex").write_text("texto", encoding="utf-8")
    (relatorio / "numeros.tex").write_text("\\newcommand{\\NumX}{80,0\\%}", encoding="utf-8")
    (relatorio / "tabelas" / "resultados_por_condicao.tex").write_text("Com RAG & 80,0\\% \\\\", encoding="utf-8")

    textos = textos_do_relatorio(relatorio, tmp_path)

    # macros e linhas de tabela são escritas por script, com dígitos de propósito
    assert sorted(textos) == ["relatorio/relatorio.tex", "relatorio/secoes/resultados.tex"]

# -*- coding: utf-8 -*-
"""Testes das regras de extração (sem abrir o PDF, exceto o teste marcado `lento`)."""

from pathlib import Path

import pytest

from rag_sus.extracao import (
    EstadoSecao,
    Linha,
    anexar_legendas_de_tabela,
    classificar_linhas,
    juntar_linhas,
    normalizar,
    pagina_impressa,
    serializar_tabela,
)
from rag_sus.modelos import Bloco

PDF = Path(__file__).resolve().parents[1] / "dados" / "relatorio_fonte.pdf"


def corpo(texto, x0=85.0, top=0.0):
    return Linha(texto, 10.9, False, x0, top)


def test_pagina_impressa_e_a_do_pdf_menos_um():
    assert pagina_impressa(7) == 6


def test_normalizar_desfaz_ligadura():
    assert normalizar("ﬁrme") == "firme"


def test_juntar_linhas_desfaz_hifenizacao_so_antes_de_minuscula():
    assert juntar_linhas(["os fi-", "lantrópicos"]) == "os filantrópicos"
    assert juntar_linhas(["custo em R$-", "Mil"]) == "custo em R$- Mil"


def test_paragrafo_novo_comeca_no_recuo():
    linhas = [
        corpo("Primeira linha do parágrafo um,", 102),
        corpo("continuação do parágrafo um."),
        corpo("Começo do parágrafo dois,", 102),
        corpo("continuação do dois."),
    ]
    blocos = [b for _, b in classificar_linhas(linhas, EstadoSecao())]

    assert [b.texto for b in blocos] == [
        "Primeira linha do parágrafo um, continuação do parágrafo um.",
        "Começo do parágrafo dois, continuação do dois.",
    ]


def test_titulo_define_a_secao_e_atravessa_paginas():
    estado = EstadoSecao()
    linhas = [
        Linha("1 A rede inteira", 14.3, True, 85, 0),
        Linha("1.4 Complexidade e porte", 12.0, True, 85, 10),
        corpo("Texto da seção.", 102, 20),
    ]
    blocos = classificar_linhas(linhas, estado)
    assert blocos[0][1].secao == "1 A rede inteira > 1.4 Complexidade e porte"

    seguinte = classificar_linhas([corpo("Continua na outra página.", 102)], estado)
    assert seguinte[0][1].secao == "1 A rede inteira > 1.4 Complexidade e porte"


def test_titulo_de_capitulo_zera_a_secao():
    estado = EstadoSecao(capitulo="1 A rede", secao="1.11 Estratos")
    classificar_linhas([Linha("2 Tabela SUS Paulista", 14.3, True, 85, 0)], estado)
    assert estado.rotulo == "2 Tabela SUS Paulista"


def test_titulo_em_duas_linhas_e_um_titulo_so():
    estado = EstadoSecao()
    classificar_linhas(
        [Linha("1 A rede inteira: o retrato e por que nem todos", 14.3, True, 85, 0),
         Linha("fazem a mesma coisa", 14.3, True, 107, 10)],
        estado,
    )
    assert estado.capitulo == "1 A rede inteira: o retrato e por que nem todos fazem a mesma coisa"


def test_negrito_do_corpo_nao_e_titulo():
    linhas = [Linha("A resposta curta tem duas metades.", 10.9, True, 102, 0)]
    blocos = classificar_linhas(linhas, EstadoSecao())
    assert blocos[0][1].tipo == "paragrafo"


def test_legenda_se_separa_do_corpo_e_rotulo_de_painel_some():
    linhas = [
        Linha("(a) Mortalidade geral", 9.0, False, 259, 0),
        Linha("Figura 5: Distribuição da mortalidade", 10.0, False, 85, 10),
        Linha("e do tempo médio de permanência.", 10.0, False, 85, 20),
        corpo("O texto volta.", 102, 30),
    ]
    blocos = [b for _, b in classificar_linhas(linhas, EstadoSecao())]

    assert [b.tipo for b in blocos] == ["legenda", "paragrafo"]
    assert blocos[0].texto == "Figura 5: Distribuição da mortalidade e do tempo médio de permanência."


def test_linha_so_de_simbolos_nao_interrompe_a_legenda():
    # Tabela 11 (p. 64): os ícones de sim/não da legenda saem numa linha própria.
    linhas = [
        Linha("Tabela 11: Mediana por estrato. A ordenação é sempre", 10.0, False, 85, 143),
        Linha("∙ ∙ ∙", 8.0, False, 300, 150),
        Linha("pela mediana. Na última coluna, sim não.", 10.0, False, 85, 155),
    ]
    blocos = [b for _, b in classificar_linhas(linhas, EstadoSecao())]

    assert [b.tipo for b in blocos] == ["legenda"]
    assert blocos[0].texto.endswith("pela mediana. Na última coluna, sim não.")


def test_pontilhado_do_sumario_e_removido():
    blocos = classificar_linhas([corpo("1.1 Qualidade dos registros . . . . . . . 12")], EstadoSecao())
    assert blocos[0][1].texto == "1.1 Qualidade dos registros"


def test_serializar_tabela_leva_o_nome_da_coluna_a_cada_celula():
    linhas = [
        ["Rede", "Taxa de\nocupação", "TMP"],
        ["Filantrópico", "63,2%", "4,1"],
        ["OSS", "78,0%", None],
    ]
    assert serializar_tabela(linhas, "Tabela 10: Medianas por rede.") == (
        "Tabela 10: Medianas por rede.\n"
        "Filantrópico: Taxa de ocupação: 63,2%; TMP: 4,1\n"
        "OSS: Taxa de ocupação: 78,0%"
    )


def test_serializar_tabela_com_cabecalho_em_duas_linhas_e_rotulo_herdado():
    # Forma da Tabela 2 (p. 25): grupo de colunas na primeira linha e linha
    # "média" sem rótulo, que herda "Direta" da linha de cima.
    linhas = [
        ["", "", "", "TMP", "Faturam. real"],
        ["Categoria", "", "Mortalidade", "(dias)", "(R$)"],
        ["Direta", "mediana", "0,0593", "5,77", "1.270"],
        ["", "média", "0,0559", "6,13", "1.411"],
    ]
    assert serializar_tabela(linhas) == (
        "Direta, mediana: Mortalidade: 0,0593; TMP (dias): 5,77; Faturam. real (R$): 1.270\n"
        "Direta, média: Mortalidade: 0,0559; TMP (dias): 6,13; Faturam. real (R$): 1.411"
    )


def test_serializar_tabela_linha_de_grupo_entra_no_rotulo():
    # Forma das listas de hospitais (p. 121): "OSS" sozinho numa linha.
    linhas = [
        ["CNES", "Hospital", "Nota"],
        ["OSS", None, None],
        ["5718368", "Hospital Municipal M'Boi Mirim", "0,914"],
        ["Filantrópico", None, None],
        ["2080664", "Santa Casa De Tupa", "0,886"],
    ]
    assert serializar_tabela(linhas) == (
        "OSS — 5718368: Hospital: Hospital Municipal M'Boi Mirim; Nota: 0,914\n"
        "Filantrópico — 2080664: Hospital: Santa Casa De Tupa; Nota: 0,886"
    )


def test_serializar_tabela_com_colunas_desalinhadas_lista_os_valores_em_ordem():
    # Forma da Tabela 15 (p. 93): a margem "5,160 a 6,186" vira três células.
    linhas = [
        ["Indicador e rede", "Nesta rede", "Margem (95%)", "Demonstrada?"],
        ["Tempo de permanência nas OSS: 5,155 dias", None, None, None, None, None],
        ["na administração Direta", "5,650", "5,160", "a", "6,186", "∙\nsim"],
    ]
    assert serializar_tabela(linhas) == (
        "Colunas: Indicador e rede | Nesta rede | Margem (95%) | Demonstrada?\n"
        "Tempo de permanência nas OSS: 5,155 dias — na administração Direta: "
        "5,650 | 5,160 | a | 6,186 | ∙ sim"
    )


def test_legenda_de_tabela_vira_primeira_linha_da_tabela():
    blocos = [
        (10.0, Bloco("legenda", "Tabela 12: Indicadores do bloco.", "2")),
        (50.0, Bloco("tabela", "Cirurgias: 434.679", "2")),
        (5.0, Bloco("paragrafo", "Texto antes.", "2")),
    ]
    saida = anexar_legendas_de_tabela(blocos)

    assert [b.tipo for b in saida] == ["paragrafo", "tabela"]
    assert saida[1].texto == "Tabela 12: Indicadores do bloco.\nCirurgias: 434.679"


def test_tabela_que_continua_na_pagina_seguinte_herda_a_legenda():
    from rag_sus.extracao import marcar_continuacoes
    from rag_sus.modelos import Pagina

    p135 = Pagina(136, 135, (Bloco("tabela", "Tabela A.1: Os 35 hospitais.\nHospital X: Leitos: 94", "A"),))
    p136 = Pagina(137, 136, (Bloco("tabela", "Hospital Y: Leitos: 68", "A"),
                             Bloco("paragrafo", "Texto depois.", "A")))

    saida = marcar_continuacoes([p135, p136])

    assert saida[1].blocos[0].texto == "Tabela A.1 (continuação): Os 35 hospitais.\nHospital Y: Leitos: 68"
    assert saida[0] == p135


def test_continuacao_vale_mesmo_com_texto_depois_da_tabela_na_pagina_anterior():
    from rag_sus.extracao import marcar_continuacoes
    from rag_sus.modelos import Pagina

    p135 = Pagina(136, 135, (Bloco("tabela", "Tabela A.1: Lista.\nX: 1", "A"),
                             Bloco("paragrafo", "Nota depois da tabela.", "A")))
    p136 = Pagina(137, 136, (Bloco("tabela", "Y: 2", "A"),))

    assert marcar_continuacoes([p135, p136])[1].blocos[0].texto.startswith("Tabela A.1 (continuação)")


def test_tabela_sem_legenda_que_nao_abre_a_pagina_fica_como_esta():
    from rag_sus.extracao import marcar_continuacoes
    from rag_sus.modelos import Pagina

    p1 = Pagina(10, 9, (Bloco("tabela", "Tabela 3: Algo.\nA: 1", "s"),))
    p2 = Pagina(11, 10, (Bloco("paragrafo", "Texto.", "s"), Bloco("tabela", "B: 2", "s")))

    assert marcar_continuacoes([p1, p2])[1] == p2


@pytest.mark.lento
@pytest.mark.skipif(not PDF.exists(), reason="PDF do Relatório-fonte ausente")
def test_extracao_real_da_pagina_da_tabela_12():
    from rag_sus.extracao import extrair_paginas

    paginas = {p.pagina_impressa: p for p in extrair_paginas(PDF)}

    assert len(paginas) == 174  # 175 do PDF menos a capa
    tabela = [b for b in paginas[70].blocos if b.tipo == "tabela"]
    assert tabela and tabela[0].texto.startswith("Tabela 12:")
    assert "434.679 em 2025" in tabela[0].texto
    sumario = " ".join(b.texto for b in paginas[6].blocos)
    assert "32,9% mais" in sumario

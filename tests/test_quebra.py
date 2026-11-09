# -*- coding: utf-8 -*-
"""Testes da quebra das páginas em Trechos.

As regras testadas vêm de docs/DESENHO.md: nenhum Trecho atravessa a página,
o texto é quebrado por parágrafo até um tamanho-alvo com sobreposição, o
título da seção abre cada Trecho, e tabela e legenda viram Trechos próprios.
"""

import pytest

from rag_sus.modelos import Bloco, Pagina
from rag_sus.quebra import contar_palavras, quebrar


def paragrafo(n_palavras: int, rotulo: str = "p") -> Bloco:
    """Parágrafo com `n_palavras` palavras numeradas, em frases de 10 palavras.

    Cada frase começa com "Frase" (maiúscula), como frase de verdade; sem isso,
    o divisor não reconhece o fim de frase e o teste mede o corte por palavra.
    """
    palavras = [f"{rotulo}{i}" for i in range(n_palavras)]
    frases = ["Frase " + " ".join(palavras[i : i + 10]) + "." for i in range(0, n_palavras, 10)]
    return Bloco("paragrafo", " ".join(frases), secao="1.4 Complexidade e porte")


def pagina(blocos, pdf=12, impressa=11) -> Pagina:
    return Pagina(pagina_pdf=pdf, pagina_impressa=impressa, blocos=tuple(blocos))


class TestFronteiraDePagina:
    def test_trechos_de_paginas_diferentes_nunca_se_misturam(self):
        p1 = pagina([paragrafo(30, "a")], pdf=12, impressa=11)
        p2 = pagina([paragrafo(30, "b")], pdf=13, impressa=12)

        trechos = quebrar([p1, p2], alvo=200, sobreposicao=20)

        assert [t.pagina_impressa for t in trechos] == [11, 12]
        assert "b0" not in trechos[0].texto
        assert "a0" not in trechos[1].texto

    def test_trecho_guarda_as_duas_paginas(self):
        trechos = quebrar([pagina([paragrafo(20)], pdf=64, impressa=63)], alvo=200, sobreposicao=0)

        assert trechos[0].pagina_impressa == 63
        assert trechos[0].pagina_pdf == 64


class TestTamanho:
    def test_paragrafos_curtos_da_mesma_pagina_se_juntam_ate_o_alvo(self):
        blocos = [paragrafo(40, "a"), paragrafo(40, "b"), paragrafo(40, "c")]

        trechos = quebrar([pagina(blocos)], alvo=100, sobreposicao=0)

        # a+b cabem em 100; c abre um Trecho novo.
        assert len(trechos) == 2
        assert "a0" in trechos[0].texto and "b0" in trechos[0].texto
        assert "c0" in trechos[1].texto and "a0" not in trechos[1].texto

    def test_paragrafo_maior_que_o_alvo_e_dividido_por_frase(self):
        trechos = quebrar([pagina([paragrafo(250)])], alvo=100, sobreposicao=0)

        assert len(trechos) >= 3
        for t in trechos:
            # o corpo (sem a linha da seção) respeita o alvo
            corpo = t.texto.split("\n", 1)[1]
            assert contar_palavras(corpo) <= 100
            assert corpo.endswith(".")  # corta em fim de frase

    def test_nenhuma_palavra_se_perde(self):
        trechos = quebrar([pagina([paragrafo(250)])], alvo=100, sobreposicao=0)

        juntos = " ".join(t.texto for t in trechos)
        for i in range(250):
            assert f"p{i}" in juntos


class TestSobreposicao:
    def test_trecho_seguinte_repete_o_fim_do_anterior(self):
        # frases de 11 palavras ("Frase" + 10): sobreposição de 15 cabe uma frase.
        trechos = quebrar([pagina([paragrafo(200)])], alvo=100, sobreposicao=15)

        assert len(trechos) >= 2
        ultima_frase_do_primeiro = trechos[0].texto.rstrip().rsplit(".", 2)[-2].split()[-1]
        assert ultima_frase_do_primeiro in trechos[1].texto

    def test_sobreposicao_nao_atravessa_a_pagina(self):
        p1 = pagina([paragrafo(30, "a")], pdf=12, impressa=11)
        p2 = pagina([paragrafo(30, "b")], pdf=13, impressa=12)

        trechos = quebrar([p1, p2], alvo=200, sobreposicao=20)

        assert "a29" not in trechos[1].texto


class TestSecao:
    def test_titulo_da_secao_abre_o_trecho(self):
        trechos = quebrar([pagina([paragrafo(20)])], alvo=200, sobreposicao=0)

        assert trechos[0].texto.startswith("1.4 Complexidade e porte\n")
        assert trechos[0].secao == "1.4 Complexidade e porte"

    def test_mudanca_de_secao_na_mesma_pagina_abre_trecho_novo(self):
        b1 = Bloco("paragrafo", "Fim da seção anterior.", secao="1.3 Perfil")
        b2 = Bloco("paragrafo", "Começo da seção nova.", secao="1.4 Complexidade")

        trechos = quebrar([pagina([b1, b2])], alvo=200, sobreposicao=20)

        assert [t.secao for t in trechos] == ["1.3 Perfil", "1.4 Complexidade"]
        assert "Fim da seção anterior" not in trechos[1].texto

    def test_trecho_sem_secao_nao_ganha_linha_vazia(self):
        b = Bloco("paragrafo", "Texto da capa interna.", secao="")

        trechos = quebrar([pagina([b])], alvo=200, sobreposicao=0)

        assert trechos[0].texto == "Texto da capa interna."


class TestTabelaELegenda:
    def test_legenda_vira_trecho_proprio(self):
        leg = Bloco("legenda", "Figura 5: Distribuição da mortalidade.", secao="1.2 Indicadores")
        blocos = [paragrafo(20, "a"), leg, paragrafo(20, "b")]

        trechos = quebrar([pagina(blocos)], alvo=200, sobreposicao=0)

        tipos = [t.tipo for t in trechos]
        assert tipos.count("legenda") == 1
        trecho_leg = trechos[tipos.index("legenda")]
        assert "Figura 5" in trecho_leg.texto
        assert "a0" not in trecho_leg.texto and "b0" not in trecho_leg.texto

    def test_tabela_vira_trecho_proprio_e_nao_se_junta_ao_texto(self):
        tab = Bloco("tabela", "Tabela 12: Indicadores.\nCirurgias: 434.679 em 2025", secao="2.3")
        blocos = [paragrafo(20, "a"), tab]

        trechos = quebrar([pagina(blocos)], alvo=200, sobreposicao=0)

        assert [t.tipo for t in trechos] == ["texto", "tabela"]
        assert "434.679" in trechos[1].texto

    def test_tabela_longa_e_dividida_por_linha_repetindo_o_cabecalho(self):
        linhas = [f"Hospital {i}: escore 0,{i:03d}" for i in range(60)]
        texto = "Tabela A.1: Lista de hospitais.\n" + "\n".join(linhas)
        tab = Bloco("tabela", texto, secao="Apêndice A")

        trechos = quebrar([pagina([tab])], alvo=100, sobreposicao=0)

        assert len(trechos) >= 2
        assert all(t.tipo == "tabela" for t in trechos)
        assert all("Tabela A.1: Lista de hospitais." in t.texto for t in trechos)
        juntos = "\n".join(t.texto for t in trechos)
        assert all(linha in juntos for linha in linhas)


class TestIdentificadores:
    def test_ids_sao_unicos_e_estaveis(self):
        paginas = [pagina([paragrafo(250)], pdf=12, impressa=11)]

        a = quebrar(paginas, alvo=100, sobreposicao=10)
        b = quebrar(paginas, alvo=100, sobreposicao=10)

        assert [t.id for t in a] == [t.id for t in b]
        assert len({t.id for t in a}) == len(a)
        assert a[0].id.startswith("p011-")


class TestParametros:
    def test_sobreposicao_maior_que_alvo_e_recusada(self):
        with pytest.raises(ValueError):
            quebrar([], alvo=50, sobreposicao=50)


def test_contar_palavras():
    assert contar_palavras("  um  dois\ntrês ") == 3
    assert contar_palavras("") == 0

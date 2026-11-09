# -*- coding: utf-8 -*-
"""Testes da busca de Trechos.

A busca é exata (ADR 0001): a mesma Pergunta recupera sempre os mesmos
Trechos, na mesma ordem. Os testes usam um embutidor falso, por contagem de
palavras, para não depender do modelo de embeddings (2,24 GB).
"""

import hashlib

import numpy as np
import pytest

from rag_sus.busca import E5Embutidor, IndiceDeTrechos
from rag_sus.modelos import Trecho


class EmbutidorDePalavras:
    """Saco de palavras com hash: textos com palavras em comum ficam próximos."""

    nome = "falso-palavras-64"
    dimensao = 64

    def _vetor(self, texto: str) -> np.ndarray:
        v = np.zeros(self.dimensao, dtype=np.float32)
        for palavra in texto.lower().split():
            h = int(hashlib.md5(palavra.strip(".,:;").encode()).hexdigest(), 16)
            v[h % self.dimensao] += 1.0
        return v

    def embutir_trechos(self, textos):
        return np.stack([self._vetor(t) for t in textos])

    def embutir_pergunta(self, texto):
        return self._vetor(texto)


def trecho(id_, texto, pagina=10):
    return Trecho(id=id_, texto=texto, pagina_impressa=pagina, pagina_pdf=pagina + 1, tipo="texto")


TRECHOS = [
    trecho("a", "mortalidade geral dos hospitais filantrópicos", 18),
    trecho("b", "taxa de ocupação de leitos de UTI nas OSS", 25),
    trecho("c", "faturamento por saída corrigido pelo IPCA", 46),
    trecho("d", "tempo médio de permanência em dias", 19),
]


@pytest.fixture
def indice():
    return IndiceDeTrechos.construir(TRECHOS, EmbutidorDePalavras())


def test_recupera_primeiro_o_trecho_mais_parecido(indice):
    resultados = indice.buscar("qual a ocupação de UTI nas OSS?", EmbutidorDePalavras(), k=2)

    assert resultados[0].trecho.id == "b"
    assert len(resultados) == 2


def test_resultados_vem_em_ordem_decrescente_de_pontuacao(indice):
    resultados = indice.buscar("mortalidade dos hospitais", EmbutidorDePalavras(), k=4)

    pontuacoes = [r.pontuacao for r in resultados]
    assert pontuacoes == sorted(pontuacoes, reverse=True)
    assert all(-1.0001 <= p <= 1.0001 for p in pontuacoes)  # cosseno


def test_busca_e_deterministica(indice):
    a = indice.buscar("faturamento IPCA", EmbutidorDePalavras(), k=3)
    b = indice.buscar("faturamento IPCA", EmbutidorDePalavras(), k=3)

    assert [(r.trecho.id, r.pontuacao) for r in a] == [(r.trecho.id, r.pontuacao) for r in b]


def test_k_maior_que_o_indice_devolve_todos(indice):
    assert len(indice.buscar("hospitais", EmbutidorDePalavras(), k=50)) == len(TRECHOS)


def test_salvar_e_carregar_preserva_os_resultados(indice, tmp_path):
    indice.salvar(tmp_path)
    recarregado = IndiceDeTrechos.carregar(tmp_path, EmbutidorDePalavras())

    a = indice.buscar("tempo de permanência", EmbutidorDePalavras(), k=4)
    b = recarregado.buscar("tempo de permanência", EmbutidorDePalavras(), k=4)
    assert [r.trecho for r in a] == [r.trecho for r in b]
    assert np.allclose([r.pontuacao for r in a], [r.pontuacao for r in b])


def test_carregar_com_outro_modelo_de_embeddings_e_recusado(indice, tmp_path):
    indice.salvar(tmp_path)

    class Outro(EmbutidorDePalavras):
        nome = "outro-modelo"

    with pytest.raises(ValueError, match="modelo"):
        IndiceDeTrechos.carregar(tmp_path, Outro())


def test_indice_vazio_e_recusado():
    with pytest.raises(ValueError):
        IndiceDeTrechos.construir([], EmbutidorDePalavras())


def test_paginas_recuperadas(indice):
    resultados = indice.buscar("ocupação de UTI", EmbutidorDePalavras(), k=2)
    assert IndiceDeTrechos.paginas(resultados)[0] == 25


class ModeloFalso:
    """Registra o que o E5Embutidor manda ao modelo do fastembed."""

    def __init__(self):
        self.recebido = []

    def embed(self, textos, **_):
        textos = list(textos)
        self.recebido.extend(textos)
        return [np.ones(3, dtype=np.float32) for _ in textos]


def test_e5_poe_os_prefixos_que_o_modelo_exige():
    modelo = ModeloFalso()
    e5 = E5Embutidor(modelo=modelo)

    e5.embutir_trechos(["texto do relatório"])
    e5.embutir_pergunta("quantos hospitais?")

    assert modelo.recebido == ["passage: texto do relatório", "query: quantos hospitais?"]

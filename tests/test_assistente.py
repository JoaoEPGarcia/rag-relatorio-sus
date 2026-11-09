# -*- coding: utf-8 -*-
"""Testes da montagem das três Condições, com um provedor falso (sem API)."""

import pytest

from rag_sus.assistente import Assistente
from rag_sus.busca import IndiceDeTrechos
from rag_sus.modelos import Trecho
from rag_sus.provedores import Metadados
from tests.test_busca import EmbutidorDePalavras


class ProvedorFalso:
    nome = "falso"

    def __init__(self, saida=None):
        self.chamadas = []
        self.saida = saida or {"resposta": "Foram 434.679.", "paginas_citadas": [70], "abstencao": False}

    def gerar_json(self, sistema, mensagem, esquema):
        self.chamadas.append({"sistema": sistema, "mensagem": mensagem, "esquema": esquema})
        return self.saida, Metadados("m", "m", False)


TRECHOS = [
    Trecho("p070-00", "Tabela 12\nCirurgias: 434.679 em 2025", 70, 71, "tabela"),
    Trecho("p018-00", "Figura 5: mortalidade entre 3,7% e 7,1%", 18, 19, "legenda"),
    Trecho("p006-00", "as OSS atendem 32,9% mais pacientes", 6, 7, "texto"),
]


@pytest.fixture
def indice():
    return IndiceDeTrechos.construir(TRECHOS, EmbutidorDePalavras())


def test_com_rag_manda_os_trechos_marcados_com_a_pagina(indice):
    provedor = ProvedorFalso()
    assistente = Assistente(provedor, indice, EmbutidorDePalavras(), k=2)

    r = assistente.responder("quantas cirurgias em 2025?", "com_rag")

    mensagem = provedor.chamadas[0]["mensagem"]
    assert "[página 70 | tabela]" in mensagem
    assert mensagem.rstrip().endswith("Pergunta: quantas cirurgias em 2025?")
    assert r.paginas_recuperadas[0] == 70
    assert len(r.paginas_recuperadas) == 2
    assert r.paginas_citadas == (70,)


def test_sem_rag_nao_manda_nada_do_relatorio(indice):
    provedor = ProvedorFalso()
    Assistente(provedor, indice, EmbutidorDePalavras()).responder("quantas cirurgias?", "sem_rag")

    chamada = provedor.chamadas[0]
    tudo = chamada["mensagem"] + " ".join(b["text"] for b in chamada["sistema"])
    assert "434.679" not in tudo and "página 70" not in tudo


def test_contexto_completo_poe_o_texto_no_sistema_e_nao_na_mensagem():
    provedor = ProvedorFalso()
    texto = "[página 70]\nCirurgias: 434.679 em 2025"
    r = Assistente(provedor, texto_completo=texto).responder("quantas cirurgias?", "contexto_completo")

    chamada = provedor.chamadas[0]
    assert texto in chamada["sistema"][-1]["text"]
    assert "434.679" not in chamada["mensagem"]
    assert r.paginas_recuperadas == ()


def test_prompts_nao_vazam_fatos_do_relatorio(indice):
    provedor = ProvedorFalso()
    a = Assistente(provedor, indice, EmbutidorDePalavras(), texto_completo="X")
    for condicao in ("com_rag", "sem_rag", "contexto_completo"):
        a.responder("pergunta", condicao)
    sistemas = " ".join(c["sistema"][0]["text"] for c in provedor.chamadas)
    for fato in ("275", "OSS", "Filantrópico", "3.025"):
        assert fato not in sistemas


def test_abstencao_e_paginas_vem_do_provedor():
    provedor = ProvedorFalso({"resposta": "O relatório não trata disso.", "paginas_citadas": [], "abstencao": True})

    r = Assistente(provedor, texto_completo="X").responder("orçamento de 1990?", "contexto_completo")

    assert r.abstencao and r.paginas_citadas == ()


def test_condicao_com_rag_sem_indice_e_recusada():
    with pytest.raises(ValueError):
        Assistente(ProvedorFalso()).responder("p", "com_rag")

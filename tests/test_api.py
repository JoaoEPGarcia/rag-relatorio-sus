# -*- coding: utf-8 -*-
"""Testes da API com assistente, índice e provedor falsos."""

from fastapi.testclient import TestClient

from rag_sus.api import criar_app
from rag_sus.assistente import Assistente
from rag_sus.busca import IndiceDeTrechos
from tests.test_assistente import TRECHOS, ProvedorFalso
from tests.test_busca import EmbutidorDePalavras


def cliente(provedor=None):
    indice = IndiceDeTrechos.construir(TRECHOS, EmbutidorDePalavras())
    assistente = Assistente(provedor or ProvedorFalso(), indice, EmbutidorDePalavras(), k=2)
    return TestClient(criar_app(assistente))


def test_saude_informa_trechos_indexados():
    with cliente() as c:
        assert c.get("/saude").json() == {"status": "ok", "trechos_indexados": 3}


def test_perguntar_devolve_resposta_paginas_e_trechos():
    with cliente() as c:
        r = c.post("/perguntar", json={"pergunta": "quantas cirurgias em 2025?"})

    assert r.status_code == 200
    corpo = r.json()
    assert corpo["resposta"] == "Foram 434.679."
    assert corpo["paginas_citadas"] == [70]
    assert corpo["trechos"][0]["pagina"] == 70
    assert len(corpo["trechos"]) == 2


def test_pergunta_curta_demais_e_recusada():
    with cliente() as c:
        assert c.post("/perguntar", json={"pergunta": "?"}).status_code == 422


def test_falha_do_modelo_vira_502_sem_detalhes_internos():
    class ProvedorQueFalha(ProvedorFalso):
        def gerar_json(self, *a):
            raise RuntimeError("chave sk-ant-segredo inválida")

    with cliente(ProvedorQueFalha()) as c:
        r = c.post("/perguntar", json={"pergunta": "quantas cirurgias?"})

    assert r.status_code == 502
    assert "segredo" not in r.text

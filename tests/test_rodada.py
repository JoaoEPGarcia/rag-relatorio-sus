# -*- coding: utf-8 -*-
"""Testes da execução de uma Rodada e da consolidação dos Veredictos."""

import csv

import pytest

from rag_sus.assistente import RespostaAssistente
from rag_sus.avaliacao.gabarito import ItemGabarito
from rag_sus.avaliacao.juiz import Veredicto
from rag_sus.avaliacao.rodada import (
    RevisaoIncompleta,
    carregar_linhas,
    consolidar,
    executar_rodada,
    gravar_folha_de_revisao,
)
from rag_sus.provedores import Metadados


def item(id_, tipo="numero_prosa", valores=(434679.0,), paginas=(70,), resposta="434.679"):
    return ItemGabarito(id_, f"pergunta {id_}?", tipo, resposta, valores, paginas, "MF")


class AssistenteFalso:
    def __init__(self, respostas):
        self.respostas = respostas  # id da pergunta -> (texto, páginas citadas, abstenção, recuperadas)
        self.chamadas = 0

    def responder(self, pergunta, condicao):
        self.chamadas += 1
        id_ = pergunta.split()[1].rstrip("?")
        texto, citadas, abst, recup = self.respostas[id_]
        return RespostaAssistente(condicao, texto, citadas, abst, recup, (), Metadados("m", "m", False, 100, 20))


class JuizFalso:
    def __init__(self, acerto=True):
        self.acerto = acerto
        self.chamadas = 0

    def julgar(self, pergunta, gabarito, resposta):
        self.chamadas += 1
        return Veredicto(self.acerto, "justificativa falsa", Metadados("j", "j", False))


def test_numerica_certa_nao_vai_ao_juiz(tmp_path):
    juiz = JuizFalso()
    a = AssistenteFalso({"G01": ("Foram 434.679 cirurgias.", (70,), False, (70, 12))})

    executar_rodada([item("G01")], "com_rag", a, juiz, tmp_path / "r.jsonl")

    linha = carregar_linhas(tmp_path / "r.jsonl")[0]
    assert linha["acerto_regra"] is True and linha["veredicto_juiz"] is None
    assert linha["acerto_citacao"] and linha["acerto_recuperacao"]
    assert juiz.chamadas == 0


def test_numerica_que_a_regra_reprova_vai_ao_juiz(tmp_path):
    juiz = JuizFalso(acerto=False)
    a = AssistenteFalso({"G01": ("Foram 434 mil cirurgias.", (70,), False, (70,))})

    executar_rodada([item("G01")], "com_rag", a, juiz, tmp_path / "r.jsonl")

    linha = carregar_linhas(tmp_path / "r.jsonl")[0]
    assert linha["acerto_regra"] is False and linha["veredicto_juiz"] is False
    assert juiz.chamadas == 1


def test_sem_resposta_e_pontuada_pela_abstencao_sem_juiz(tmp_path):
    juiz = JuizFalso()
    sem = item("G51", tipo="sem_resposta", valores=(), paginas=(), resposta="Não trata.")
    a = AssistenteFalso({"G51": ("O relatório não trata disso.", (), True, (3,))})

    executar_rodada([sem], "com_rag", a, juiz, tmp_path / "r.jsonl")

    linha = carregar_linhas(tmp_path / "r.jsonl")[0]
    assert linha["acerto_regra"] is True and juiz.chamadas == 0
    assert linha["acerto_recuperacao"] is None


def test_rodada_e_retomavel_sem_repetir_perguntas_ja_respondidas(tmp_path):
    destino = tmp_path / "r.jsonl"
    respostas = {
        "G01": ("Foram 434.679.", (70,), False, (70,)),
        "G02": ("Foram 434.679.", (70,), False, (70,)),
    }
    a = AssistenteFalso(respostas)
    executar_rodada([item("G01")], "com_rag", a, JuizFalso(), destino)
    executar_rodada([item("G01"), item("G02")], "com_rag", a, JuizFalso(), destino)

    assert a.chamadas == 2
    assert [l["id"] for l in carregar_linhas(destino)] == ["G01", "G02"]


def test_sem_recuperacao_nas_condicoes_sem_rag(tmp_path):
    a = AssistenteFalso({"G01": ("Foram 434.679.", (70,), False, ())})

    executar_rodada([item("G01")], "sem_rag", a, JuizFalso(), tmp_path / "r.jsonl")

    assert carregar_linhas(tmp_path / "r.jsonl")[0]["acerto_recuperacao"] is None


class TestConsolidacao:
    def _rodada(self, tmp_path):
        destino = tmp_path / "r.jsonl"
        conceito = item("G41", tipo="conceito", valores=(), resposta="Mede eficiência.")
        a = AssistenteFalso({
            "G01": ("Foram 434.679.", (70,), False, (70,)),
            "G41": ("Mede a eficiência técnica.", (99,), False, (160,)),
        })
        executar_rodada([item("G01"), conceito], "com_rag", a, JuizFalso(True), destino)
        return destino

    def test_folha_de_revisao_lista_so_os_veredictos_do_juiz(self, tmp_path):
        destino = self._rodada(tmp_path)
        folha = tmp_path / "revisao.csv"

        gravar_folha_de_revisao([destino], folha)

        with open(folha, encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
        assert [l["id"] for l in linhas] == ["G41"]
        assert linhas[0]["veredicto_revisado"] == ""

    def test_consolidar_exige_revisao_de_todos_os_veredictos_do_juiz(self, tmp_path):
        destino = self._rodada(tmp_path)
        folha = tmp_path / "revisao.csv"
        gravar_folha_de_revisao([destino], folha)

        with pytest.raises(RevisaoIncompleta, match="G41"):
            consolidar(destino, folha, exigir_revisao=True)

    def test_revisao_do_autor_vence_o_juiz(self, tmp_path):
        destino = self._rodada(tmp_path)
        folha = tmp_path / "revisao.csv"
        gravar_folha_de_revisao([destino], folha)
        texto = folha.read_text(encoding="utf-8").replace(",,", ",errado,", 1)
        folha.write_text(texto, encoding="utf-8")

        finais = {l["id"]: l for l in consolidar(destino, folha, exigir_revisao=True)}

        assert finais["G01"]["acerto_resposta"] is True  # regra numérica
        assert finais["G41"]["acerto_resposta"] is False  # o autor discordou do Juiz
        assert finais["G41"]["classe_erro"] == "falha de recuperação"

    def test_regravar_a_folha_preserva_o_que_o_autor_ja_revisou(self, tmp_path):
        destino = self._rodada(tmp_path)
        folha = tmp_path / "revisao.csv"
        gravar_folha_de_revisao([destino], folha)
        folha.write_text(folha.read_text(encoding="utf-8").replace(",,", ",certo,", 1), encoding="utf-8")

        gravar_folha_de_revisao([destino], folha)

        with open(folha, encoding="utf-8") as f:
            assert list(csv.DictReader(f))[0]["veredicto_revisado"] == "certo"

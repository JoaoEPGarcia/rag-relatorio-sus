# -*- coding: utf-8 -*-
"""Testes do registro de números e da formatação em português."""

import json

import pytest

from rag_sus.numeros import Numero, carregar, formatar, registrar, registrar_do_script


@pytest.mark.parametrize(
    "valor,formato,esperado",
    [
        (1236, "inteiro", "1.236"),
        (275, "inteiro", "275"),
        (1_000_000, "inteiro", "1.000.000"),
        (0.8, "pct1", "80,0%"),
        (0.0833, "pct1", "8,3%"),
        (0.12345, "pp1", "12,3 p.p."),
        (-0.05, "pp1", "−5,0 p.p."),
        (0.0593, "dec4", "0,0593"),
        (4.3, "dec2", "4,30"),
        (0.0321, "p3", "0,032"),
        (0.0004, "p3", "< 0,001"),
        (2.5, "usd2", "US$ 2,50"),
        (2025, "ano", "2025"),
    ],
)
def test_formatar_em_portugues(valor, formato, esperado):
    assert formatar(valor, formato) == esperado


def test_formato_desconhecido_e_recusado():
    with pytest.raises(ValueError):
        formatar(1, "chute")


def test_registrar_acumula_e_substitui_pela_chave(tmp_path):
    caminho = tmp_path / "numeros.json"

    registrar("a", 10, "dez", "s1.py", caminho=caminho)
    registrar("b", 0.5, "metade", "s2.py", formato="pct1", caminho=caminho)
    registrar("a", 11, "onze", "s1.py", caminho=caminho)

    dados = carregar(caminho)
    assert dados["a"] == {"valor": 11, "texto": "11", "descricao": "onze", "script": "s1.py", "formato": "inteiro"}
    assert dados["b"]["texto"] == "50,0%"
    # arquivo ordenado por chave: diff estável entre execuções
    assert list(json.loads(caminho.read_text(encoding="utf-8"))) == ["a", "b"]


def test_float_sem_formato_e_recusado(tmp_path):
    with pytest.raises(ValueError, match="formato"):
        registrar("x", 0.5, "meio", "s.py", caminho=tmp_path / "n.json")


def test_chave_precisa_ser_identificador_simples(tmp_path):
    # a chave vira macro LaTeX e marcador {{chave}} no README
    with pytest.raises(ValueError):
        registrar("acerto-rag", 1, "x", "s.py", caminho=tmp_path / "n.json")


def test_registrar_guarda_onde_o_numero_aparece_quando_declarado(tmp_path):
    caminho = tmp_path / "numeros.json"
    registrar("acerto", 0.8, "acerto", "scripts/05_figuras.py", formato="pct1", caminho=caminho,
              aparece_em=["figuras/acerto_por_condicao.png (título)"])
    registrar("trechos", 570, "Trechos", "scripts/01_extrair.py", caminho=caminho)

    dados = carregar(caminho)
    assert dados["acerto"]["aparece_em"] == ["figuras/acerto_por_condicao.png (título)"]
    assert "aparece_em" not in dados["trechos"]


def test_registrar_do_script_troca_de_uma_vez_os_numeros_do_script(tmp_path):
    caminho = tmp_path / "numeros.json"
    registrar("corpus_trechos", 570, "Trechos", "scripts/01_extrair.py", caminho=caminho)
    registrar_do_script("scripts/04_analisar.py", [
        Numero("acerto", 0.8, "acerto", "pct1"),
        Numero("concordancia", 0.9, "concordância", "pct1"),
    ], caminho=caminho)

    # a segunda análise não tem mais repetição: a chave antiga do script some
    registrar_do_script("scripts/04_analisar.py", [
        Numero("acerto", 0.82, "acerto", "pct1", aparece_em=("relatorio/tabelas/x.tex",)),
    ], caminho=caminho)

    dados = carregar(caminho)
    assert sorted(dados) == ["acerto", "corpus_trechos"]
    assert dados["acerto"]["texto"] == "82,0%"
    assert dados["acerto"]["aparece_em"] == ["relatorio/tabelas/x.tex"]
    assert "aparece_em" not in dados["corpus_trechos"]


def test_registrar_do_script_recusa_chave_repetida(tmp_path):
    with pytest.raises(ValueError, match="repetida"):
        registrar_do_script("s.py", [Numero("a", 1, "um"), Numero("a", 2, "dois")], caminho=tmp_path / "n.json")

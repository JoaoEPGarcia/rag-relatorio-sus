# -*- coding: utf-8 -*-
"""Testes do gerador de Rodadas sintéticas de demonstração.

As figuras, o Relatório de avaliação e o pipeline são verificados sobre
estas Rodadas, numa raiz temporária, sem chamar o modelo. O que importa aqui:
a análise roda sobre elas, o resultado é sempre o mesmo para a mesma semente,
e nada sintético chega ao registro de uma cópia do projeto.
"""

import pytest

from rag_sus import numeros
from rag_sus.avaliacao.resultados import analisar
from rag_sus.avaliacao.sinteticas import RaizProibida, gerar_rodadas_sinteticas


def analisar_raiz(raiz, numeros_json=None):
    return analisar(raiz / "resultados" / "rodadas", raiz / "avaliacao" / "revisao_veredictos.csv",
                    numeros_json=numeros_json or raiz / "resultados" / "numeros.json",
                    pasta_tabelas=raiz / "relatorio" / "tabelas")


def test_rodadas_sinteticas_viram_numeros_e_tabelas(tmp_path):
    raiz = tmp_path / "raiz"
    gerar_rodadas_sinteticas(raiz, semente=7, repeticoes=2)

    analisar_raiz(raiz)

    r = numeros.carregar(raiz / "resultados" / "numeros.json")
    assert r["destaque_n_respondiveis"]["valor"] == 50
    assert r["gabarito_n_sem_resposta"]["valor"] == 10
    assert r["destaque_acerto_com_rag"]["valor"] > r["destaque_acerto_sem_rag"]["valor"]
    assert r["revisao_veredictos_revisados"]["valor"] == r["revisao_veredictos_juiz"]["valor"] > 0
    assert r["revisao_veredictos_mudados"]["valor"] > 0
    for rodada in ("repeticao1", "repeticao2"):
        for c in ("com_rag", "sem_rag", "contexto_completo"):
            assert r[f"concordancia_{rodada}_{c}_n"]["valor"] == 60
    assert sorted(p.name for p in (raiz / "relatorio" / "tabelas").iterdir()) == [
        "comparacao_pareada.tex", "custo_por_condicao.tex", "erros_por_tipo.tex", "resultados_por_condicao.tex"]


def test_mesma_semente_gera_as_mesmas_rodadas(tmp_path):
    def arquivos(raiz):
        return {p.relative_to(raiz).as_posix(): p.read_bytes() for p in sorted(raiz.rglob("*")) if p.is_file()}

    gerar_rodadas_sinteticas(tmp_path / "a", semente=3, repeticoes=1)
    gerar_rodadas_sinteticas(tmp_path / "b", semente=3, repeticoes=1)
    gerar_rodadas_sinteticas(tmp_path / "b", semente=3, repeticoes=1)  # de novo por cima: não acumula

    assert arquivos(tmp_path / "a") == arquivos(tmp_path / "b")
    assert "resultados/rodadas/repeticao2/com_rag.jsonl" not in arquivos(tmp_path / "a")


def test_gerador_recusa_gravar_numa_copia_do_projeto(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    with pytest.raises(RaizProibida):
        gerar_rodadas_sinteticas(tmp_path)


def test_rodadas_sinteticas_nao_entram_no_registro_de_uma_copia_do_projeto(tmp_path):
    raiz = tmp_path / "raiz"
    gerar_rodadas_sinteticas(raiz, repeticoes=0)
    projeto = tmp_path / "projeto"
    projeto.mkdir()
    (projeto / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    with pytest.raises(RaizProibida, match="sintéticas"):
        analisar_raiz(raiz, numeros_json=projeto / "resultados" / "numeros.json")
    assert not (projeto / "resultados").exists()

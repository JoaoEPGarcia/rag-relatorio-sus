# -*- coding: utf-8 -*-
"""Testes do gerador de Rodadas sintéticas de demonstração.

As figuras, o Relatório de avaliação e o pipeline são verificados sobre
estas Rodadas, numa raiz temporária, sem chamar o modelo. O que importa aqui:
a análise roda sobre elas, o resultado é sempre o mesmo para a mesma semente,
e nada sintético chega ao registro de uma cópia do projeto.
"""

import pytest

from rag_sus import config, numeros
from rag_sus.avaliacao.resultados import analisar
from rag_sus.avaliacao.rodada import carregar_linhas
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
        "comparacao_pareada.tex", "concordancia.tex", "custo_por_condicao.tex", "erros_por_tipo.tex",
        "resultados_por_condicao.tex"]


def test_rodadas_sinteticas_gravam_os_parametros_do_projeto_como_a_rodada_real(tmp_path):
    # o Relatório de avaliação cita o k e os modelos; na raiz sintética, são os do parametros.toml do projeto
    raiz = tmp_path / "raiz"
    gerar_rodadas_sinteticas(raiz, semente=7, repeticoes=0)

    analisar_raiz(raiz)

    r = numeros.carregar(raiz / "resultados" / "numeros.json")
    p = config.carregar_parametros(config.PROJETO / "parametros.toml")
    assert r["parametros_k"]["valor"] == p.k
    assert r["parametros_modelo_respondedor"]["texto"] == p.modelo_respondedor
    assert r["parametros_modelo_juiz"]["texto"] == p.modelo_juiz
    assert r["parametros_commit"]["texto"] == "sintetico"  # só o hash de verdade é encurtado


def test_respostas_e_juiz_sinteticos_usam_os_modelos_do_parametros_toml(tmp_path):
    original = (config.PROJETO / "parametros.toml").read_text(encoding="utf-8")
    parametros = tmp_path / "parametros.toml"
    parametros.write_text(original.replace('modelo = "', 'modelo = "outro-', 2), encoding="utf-8")
    p = config.carregar_parametros(parametros)
    raiz = tmp_path / "raiz"

    gerar_rodadas_sinteticas(raiz, repeticoes=0, parametros=parametros)

    linhas = carregar_linhas(raiz / "resultados" / "rodadas" / "principal" / "com_rag.jsonl")
    assert p.modelo_respondedor.startswith("outro-")
    assert {l["modelo_que_respondeu"] for l in linhas} == {p.modelo_respondedor}


def test_raiz_sintetica_recebe_os_numeros_reais_do_corpus(tmp_path):
    # o README pede os números do corpus, que saem do PDF real (01_extrair.py) e não das Rodadas
    do_projeto = tmp_path / "projeto_numeros.json"
    numeros.registrar("corpus_palavras", 60370, "palavras extraídas", "scripts/01_extrair.py", caminho=do_projeto)
    numeros.registrar("quebra_alvo", 180, "máximo de palavras por Trecho", "scripts/01_extrair.py",
                      caminho=do_projeto)
    numeros.registrar("destaque_acerto_com_rag", 0.9, "acerto real", "scripts/04_analisar.py", formato="pct1",
                      caminho=do_projeto)
    raiz = tmp_path / "raiz"

    gerar_rodadas_sinteticas(raiz, repeticoes=0, numeros_do_projeto=do_projeto)

    r = numeros.carregar(raiz / "resultados" / "numeros.json")
    assert sorted(r) == ["corpus_palavras", "quebra_alvo"]  # só os do corpus; nenhum resultado real
    assert (r["corpus_palavras"]["texto"], r["corpus_palavras"]["texto_en"]) == ("60.370", "60,370")
    assert r["corpus_palavras"]["script"] == "scripts/01_extrair.py"


def test_raiz_sintetica_sem_registro_do_projeto_segue_sem_os_numeros_do_corpus(tmp_path):
    raiz = tmp_path / "raiz"
    gerar_rodadas_sinteticas(raiz, repeticoes=0, numeros_do_projeto=tmp_path / "nao_existe.json")
    assert numeros.carregar(raiz / "resultados" / "numeros.json") == {}


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

# -*- coding: utf-8 -*-
"""O README gerado de README.base.md sobre as Rodadas sintéticas, numa raiz temporária.

Os scripts (06_gerar_documentos.py e conferir_numeros.py) e o README.base.md
vêm do projeto; os dados e as saídas, da raiz em RAG_SUS_RAIZ. O que importa:
nenhum marcador fica sem valor, o conferidor passa, a seção em inglês sai com
ponto decimal, e nada do projeto é escrito.
"""

import os
import subprocess
import sys

import pytest

from rag_sus import config, numeros
from rag_sus.avaliacao.resultados import analisar
from rag_sus.avaliacao.sinteticas import gerar_rodadas_sinteticas
from rag_sus.documentos import digitos_soltos_no_markdown

SAIDAS_DO_PROJETO = ("README.md", "NUMEROS_CANONICOS.md", "relatorio/numeros.tex", "resultados/numeros.json")


def rodar_script(nome, raiz):
    env = {**os.environ, "RAG_SUS_RAIZ": str(raiz), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(config.PROJETO / "scripts" / nome)], env=env, cwd=raiz,
                          capture_output=True, text=True, encoding="utf-8")


@pytest.fixture(scope="module")
def raiz_sintetica(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("raiz")
    antes = {p: (config.PROJETO / p).read_bytes() for p in SAIDAS_DO_PROJETO}
    gerar_rodadas_sinteticas(raiz, semente=2026, repeticoes=2)
    analisar(raiz / "resultados" / "rodadas", raiz / "avaliacao" / "revisao_veredictos.csv",
             numeros_json=raiz / "resultados" / "numeros.json", pasta_tabelas=raiz / "relatorio" / "tabelas")
    gerado = rodar_script("06_gerar_documentos.py", raiz)
    conferido = rodar_script("conferir_numeros.py", raiz)
    depois = {p: (config.PROJETO / p).read_bytes() for p in SAIDAS_DO_PROJETO}
    return {"raiz": raiz, "gerado": gerado, "conferido": conferido, "projeto_intacto": antes == depois}


def test_readme_sobre_a_raiz_sintetica_nao_tem_marcador_sem_valor(raiz_sintetica):
    assert raiz_sintetica["gerado"].returncode == 0, raiz_sintetica["gerado"].stdout + raiz_sintetica["gerado"].stderr
    readme = (raiz_sintetica["raiz"] / "README.md").read_text(encoding="utf-8")
    assert "{{" not in readme and "}}" not in readme


def test_conferidor_passa_sobre_a_raiz_sintetica(raiz_sintetica):
    conferido = raiz_sintetica["conferido"]
    assert conferido.returncode == 0, conferido.stdout + conferido.stderr
    assert "Conferência dos números: ok" in conferido.stdout


def test_readme_sintetico_nao_escreve_no_projeto(raiz_sintetica):
    assert raiz_sintetica["projeto_intacto"]


def test_principais_resultados_em_portugues_e_in_english_em_ingles(raiz_sintetica):
    raiz = raiz_sintetica["raiz"]
    r = numeros.carregar(raiz / "resultados" / "numeros.json")
    readme = (raiz / "README.md").read_text(encoding="utf-8")
    resultados = readme.split("## Principais resultados")[1].split("\n## ")[0]
    ingles = readme.split("## In English")[1]

    destaque = r["destaque_acerto_com_rag"]
    assert destaque["texto"] != destaque["texto_en"]  # a vírgula decimal muda para ponto
    assert f"**{destaque['texto']}**" in resultados and destaque["texto_en"] not in resultados
    assert f"**{destaque['texto_en']}**" in ingles and destaque["texto"] not in ingles
    for chave in ("com_rag_x_sem_rag_conclusao", "com_rag_x_contexto_completo_conclusao",
                  "com_rag_erro_mais_frequente"):
        assert r[chave]["texto"] in resultados
        assert r[chave]["texto_en"] in ingles


def test_readme_base_nao_tem_numero_digitado():
    base = (config.PROJETO / "README.base.md").read_text(encoding="utf-8")
    assert digitos_soltos_no_markdown(base) == []

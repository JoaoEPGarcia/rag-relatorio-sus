# -*- coding: utf-8 -*-
"""Testes dos textos das figuras: títulos, rótulos e os números que elas imprimem.

As figuras em si (matplotlib) não têm teste de unidade. O que se testa aqui é
a parte que decide o que a figura diz: o título que afirma o achado, a partir
do registro, e a lista de números impressos, que vai para o registro com a
figura em "Onde aparece". Os títulos esperados são escritos à mão.
"""

import re

from rag_sus import numeros
from rag_sus.avaliacao.figuras import textos_acerto, textos_erros

SCRIPT_04 = "scripts/04_analisar.py"


def registro(**valores):
    """Um registro mínimo: chave -> (valor, formato), como o 04_analisar.py grava."""
    return {
        chave: {"valor": v, "texto": numeros.formatar(v, f), "formato": f, "descricao": chave, "script": SCRIPT_04}
        for chave, (v, f) in valores.items()
    }


def acertos(com, sem, cc, dif_sem, dif_cc, n=50):
    """Acerto por Condição (valor, inf, sup) e as diferenças pareadas com RAG menos a outra (dif, inf, sup)."""
    valores = {"destaque_n_respondiveis": (n, "inteiro")}
    for c, (v, inf, sup) in {"com_rag": com, "sem_rag": sem, "contexto_completo": cc}.items():
        valores[f"{c}_acerto_resposta"] = (v, "pct1")
        valores[f"{c}_acerto_resposta_inf"] = (inf, "pct1")
        valores[f"{c}_acerto_resposta_sup"] = (sup, "pct1")
    for outra, (d, inf, sup) in {"sem_rag": dif_sem, "contexto_completo": dif_cc}.items():
        valores[f"com_rag_x_{outra}_diferenca"] = (d, "pp1")
        valores[f"com_rag_x_{outra}_diferenca_inf"] = (inf, "pp1")
        valores[f"com_rag_x_{outra}_diferenca_sup"] = (sup, "pp1")
    return valores


def test_titulo_do_acerto_afirma_que_com_rag_acerta_mais_quando_o_ic_da_diferenca_fica_acima_de_zero():
    r = registro(**acertos(com=(0.8, 0.67, 0.888), sem=(0.22, 0.128, 0.35), cc=(0.82, 0.69, 0.9),
                           dif_sem=(0.58, 0.42, 0.7), dif_cc=(-0.02, -0.12, 0.08)))

    t = textos_acerto(r)

    assert t.titulo == "Com RAG, o assistente acerta 80,0% das respostas, contra 22,0% sem RAG"


def test_titulo_do_acerto_declara_o_achado_nulo_quando_o_ic_da_diferenca_cruza_o_zero():
    r = registro(**acertos(com=(0.5, 0.37, 0.63), sem=(0.44, 0.31, 0.58), cc=(0.52, 0.39, 0.65),
                           dif_sem=(0.06, -0.08, 0.2), dif_cc=(-0.02, -0.12, 0.08)))

    assert textos_acerto(r).titulo == (
        "Com RAG e sem RAG, o acerto não se distingue: 50,0% contra 44,0% das respostas")


def test_titulo_do_acerto_afirma_que_sem_rag_acerta_mais_quando_o_ic_da_diferenca_fica_abaixo_de_zero():
    r = registro(**acertos(com=(0.3, 0.19, 0.44), sem=(0.6, 0.46, 0.72), cc=(0.62, 0.48, 0.74),
                           dif_sem=(-0.3, -0.45, -0.14), dif_cc=(-0.32, -0.46, -0.16)))

    assert textos_acerto(r).titulo == "Sem RAG, o assistente acerta mais: 60,0% das respostas, contra 30,0% com RAG"


NUMERO_IMPRESSO = re.compile(r"\d+(?:[.,]\d+)*")


def impressos(t):
    textos = [t.titulo, t.subtitulo, *t.rotulos.values()]
    return [m for texto in textos for m in NUMERO_IMPRESSO.findall(texto)]


def conferir_registrados(t, prefixo):
    """Todo número impresso está num Numero da figura, e todo Numero declara a figura em aparece_em."""
    textos = [numeros.formatar(n.valor, n.formato) for n in t.numeros]
    for impresso in impressos(t):
        assert any(impresso in texto for texto in textos), f"{impresso} impresso sem registro"
    for n in t.numeros:
        assert n.chave.startswith(prefixo)
        assert n.aparece_em == (t.arquivo,)


def test_figura_do_acerto_rotula_cada_condicao_com_o_ic_e_registra_o_que_imprime():
    r = registro(**acertos(com=(0.8, 0.67, 0.888), sem=(0.22, 0.128, 0.35), cc=(0.82, 0.69, 0.9),
                           dif_sem=(0.58, 0.42, 0.7), dif_cc=(-0.02, -0.12, 0.08)))

    t = textos_acerto(r)

    assert t.arquivo == "figuras/acerto_por_condicao.png"
    assert t.rotulos["com_rag"] == "80,0% (IC 67,0% a 88,8%)"
    assert t.rotulos["contexto_completo"] == "82,0% (IC 69,0% a 90,0%)"
    assert "50 Perguntas respondíveis" in t.subtitulo
    assert "95%" in t.subtitulo
    conferir_registrados(t, "figura_acerto_")
    por_chave = {n.chave: n for n in t.numeros}
    assert por_chave["figura_acerto_com_rag_acerto_resposta_inf"].valor == 0.67


TIPOS = ("numero_prosa", "numero_tabela", "numero_legenda", "conceito", "sintese")
CLASSES = ("falha_recuperacao", "falha_leitura", "abstencao_indevida", "citacao_errada")


def erros(por_tipo, inventadas=0, n=10, n_sem=10):
    """por_tipo: Tipo -> (falha de recuperação, falha de leitura, abstenção indevida, citação errada)."""
    valores = {}
    totais = dict.fromkeys(CLASSES, 0)
    for tipo in TIPOS:
        contagens = por_tipo.get(tipo, (0, 0, 0, 0))
        valores[f"com_rag_tipo_{tipo}_n"] = (n, "inteiro")
        for slug, k in zip(CLASSES, contagens, strict=True):
            valores[f"com_rag_tipo_{tipo}_{slug}"] = (k, "inteiro")
            totais[slug] += k
    valores["com_rag_tipo_sem_resposta_n"] = (n_sem, "inteiro")
    valores["com_rag_tipo_sem_resposta_resposta_inventada"] = (inventadas, "inteiro")
    for slug, k in totais.items():
        valores[f"com_rag_erros_{slug}"] = (k, "inteiro")
    valores["com_rag_erros_resposta_inventada"] = (inventadas, "inteiro")
    return valores


def test_titulo_dos_erros_aponta_a_classe_mais_comum_e_quantos_erros_ela_explica():
    r = registro(**erros({"sintese": (1, 3, 0, 0), "numero_tabela": (0, 2, 0, 1), "conceito": (1, 0, 1, 0)},
                         inventadas=1))

    t = textos_erros(r)

    assert t.titulo == "Com RAG, a falha de leitura é a Classe de erro mais comum: 5 dos 10 erros"
    assert t.destaque == ("falha_leitura",)


def test_titulo_dos_erros_declara_o_empate_entre_classes():
    r = registro(**erros({"sintese": (2, 2, 0, 0), "conceito": (0, 0, 1, 0)}))

    t = textos_erros(r)

    assert t.titulo == ("Com RAG, a falha de recuperação e a falha de leitura empatam como "
                        "Classe de erro mais comum, com 2 erros cada")
    assert t.destaque == ("falha_recuperacao", "falha_leitura")


def test_titulo_dos_erros_sem_erro_nenhum():
    assert textos_erros(registro(**erros({}))).titulo == "Com RAG, o assistente não errou nenhuma resposta nem citação"


def test_figura_dos_erros_ordena_os_tipos_pelos_erros_rotula_so_o_que_existe_e_registra_o_que_imprime():
    r = registro(**erros({"sintese": (1, 3, 0, 0), "numero_tabela": (0, 2, 0, 1), "conceito": (1, 0, 1, 0)},
                         inventadas=1))

    t = textos_erros(r)

    assert t.arquivo == "figuras/erros_por_tipo.png"
    assert t.linhas == ("sintese", "numero_tabela", "conceito", "numero_prosa", "numero_legenda", "sem_resposta")
    assert t.colunas[0] == "falha_leitura"
    assert t.rotulos["sintese"] == "Síntese entre páginas (10)"
    assert t.rotulos["sintese/falha_leitura"] == "3"
    assert t.rotulos["sem_resposta/resposta_inventada"] == "1"
    assert "numero_prosa/falha_leitura" not in t.rotulos  # zero: sem barra e sem rótulo
    assert t.rotulos["coluna/falha_leitura"] == "Falha de leitura (5)"
    conferir_registrados(t, "figura_erros_")

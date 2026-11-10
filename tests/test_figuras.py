# -*- coding: utf-8 -*-
"""Testes dos textos das figuras: títulos, rótulos e os números que elas imprimem.

As figuras em si (matplotlib) não têm teste de unidade. O que se testa aqui é
a parte que decide o que a figura diz: o título que afirma o achado, a partir
do registro, e a lista de números impressos, que vai para o registro com a
figura em "Onde aparece". Os títulos esperados são escritos à mão.
"""

import re

import pytest

from rag_sus import numeros
from rag_sus.avaliacao.figuras import (
    MAX_SUBTITULO,
    fonte_dos_dados,
    registrar_figuras,
    textos_acerto,
    textos_custo,
    textos_das_figuras,
    textos_erros,
)
from rag_sus.avaliacao.resultados import analisar
from rag_sus.avaliacao.sinteticas import RaizProibida, gerar_rodadas_sinteticas, recusar_no_projeto
from rag_sus.documentos import usos

SCRIPT_04 = "scripts/04_analisar.py"


def registro(**valores):
    """Um registro mínimo: chave -> (valor, formato), como o 04_analisar.py grava (com o nível do IC)."""
    valores = {"ic_nivel": (95, "inteiro"), **valores}
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


def conferir_registrados(t, r, prefixo):
    """Todo número impresso é uma chave do registro cujo uso a figura declara, ou um número só da figura.

    Os números da análise não são copiados: a figura declara que os usa (t.usos). Só os
    calculados pela figura (uma razão, um total) viram chaves próprias, com a figura em aparece_em.
    """
    textos = [r[chave]["texto"] for chave in t.usos] + [numeros.formatar(n.valor, n.formato) for n in t.numeros]
    for impresso in impressos(t):
        assert any(impresso in texto for texto in textos), f"{impresso} impresso sem registro"
    assert all(chave in r and not chave.startswith("figura_") for chave in t.usos)
    for n in t.numeros:
        assert n.chave.startswith(prefixo)
        assert n.aparece_em == (t.arquivo,)
        assert n.chave not in r  # nenhuma cópia de número da análise


def test_figura_do_acerto_rotula_cada_condicao_com_o_ic_e_registra_o_que_imprime():
    r = registro(**acertos(com=(0.8, 0.67, 0.888), sem=(0.22, 0.128, 0.35), cc=(0.82, 0.69, 0.9),
                           dif_sem=(0.58, 0.42, 0.7), dif_cc=(-0.02, -0.12, 0.08)))

    t = textos_acerto(r)

    assert t.arquivo == "figuras/acerto_por_condicao.png"
    assert t.rotulos["com_rag"] == "80,0% (IC 67,0% a 88,8%)"
    assert t.rotulos["contexto_completo"] == "82,0% (IC 69,0% a 90,0%)"
    assert "50 Perguntas respondíveis" in t.subtitulo
    assert "95%" in t.subtitulo
    conferir_registrados(t, r, "figura_acerto_")
    assert {"com_rag_acerto_resposta_inf", "ic_nivel", "destaque_n_respondiveis"} <= set(t.usos)
    assert t.numeros == ()  # tudo o que a figura do acerto imprime já está no registro


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
    valores["gabarito_n_perguntas"] = (len(TIPOS) * n + n_sem, "inteiro")
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
    assert "60 da Rodada principal" in t.subtitulo
    conferir_registrados(t, r, "figura_erros_")
    assert [n.chave for n in t.numeros] == ["figura_erros_total"]  # a soma dos erros só a figura calcula


def custos(acerto_com, acerto_cc, dif_cc, tokens=(2712.4, 221.0, 94010.0), latencia=(2.61, 1.62, 10.4)):
    """Acerto, diferença com RAG menos contexto completo (dif, inf, sup), tokens médios e latência mediana."""
    valores = acertos(com=(acerto_com, 0, 1), sem=(0.22, 0.12, 0.35), cc=(acerto_cc, 0, 1),
                      dif_sem=(0.58, 0.42, 0.7), dif_cc=dif_cc)
    valores["gabarito_n_perguntas"] = (60, "inteiro")
    for c, tok, lat in zip(("com_rag", "sem_rag", "contexto_completo"), tokens, latencia, strict=True):
        valores[f"{c}_tokens_entrada_medio"] = (tok, "inteiro")
        valores[f"{c}_latencia_mediana_s"] = (lat, "dec1")
    return valores


def test_titulo_do_custo_quando_o_contexto_completo_acerta_parecido_mas_le_muito_mais_tokens():
    r = registro(**custos(0.8, 0.82, dif_cc=(-0.02, -0.12, 0.08)))

    # o IC da diferença inclui o zero: a mesma leitura neutra do registro, com os dois números, e nada de "perto"
    assert textos_custo(r).titulo == (
        "Com RAG, 80,0%, contra o contexto completo, 82,0%: os dados não distinguem as duas Condições, "
        "mas o contexto completo lê 35 vezes mais tokens por Pergunta")


def test_titulo_do_custo_quando_o_contexto_completo_acerta_mais():
    r = registro(**custos(0.7, 0.86, dif_cc=(-0.16, -0.28, -0.04), tokens=(9000.0, 221.0, 60000.0)))

    assert textos_custo(r).titulo == (
        "O contexto completo acerta mais, 86,0% contra 70,0% com RAG, mas lê 6,7 vezes mais tokens por Pergunta")


def test_titulo_do_custo_quando_com_rag_acerta_mais():
    r = registro(**custos(0.86, 0.7, dif_cc=(0.16, 0.04, 0.28)))

    assert textos_custo(r).titulo == (
        "Com RAG, o assistente acerta mais que com o contexto completo, 86,0% contra 70,0%, "
        "e lê 35 vezes menos tokens por Pergunta")


def test_figura_do_custo_rotula_acerto_tokens_e_latencia_de_cada_condicao_e_registra_o_que_imprime():
    r = registro(**custos(0.8, 0.82, dif_cc=(-0.02, -0.12, 0.08)))
    t = textos_custo(r)

    assert t.arquivo == "figuras/custo_por_condicao.png"
    assert t.linhas == ("com_rag", "sem_rag", "contexto_completo")
    assert t.destaque == ("com_rag",)
    assert t.rotulos["contexto_completo"] == "Contexto completo\nacerta 82,0%"
    assert t.rotulos["com_rag/tokens"] == "média 2.712"
    assert t.rotulos["contexto_completo/latencia"] == "mediana 10,4 s"
    assert "60 Perguntas" in t.subtitulo
    conferir_registrados(t, r, "figura_custo_")
    assert [n.chave for n in t.numeros] == ["figura_custo_razao_tokens"]


def test_sobre_rodadas_sinteticas_as_tres_figuras_registram_chaves_proprias_com_a_figura_em_onde_aparece(tmp_path):
    raiz = tmp_path / "raiz"
    pasta_rodadas = gerar_rodadas_sinteticas(raiz, semente=7, repeticoes=0)
    numeros_json = raiz / "resultados" / "numeros.json"
    analisar(pasta_rodadas, raiz / "avaliacao" / "revisao_veredictos.csv", numeros_json=numeros_json,
             pasta_tabelas=raiz / "relatorio" / "tabelas")

    r = numeros.carregar(numeros_json)
    figuras = textos_das_figuras(r)

    assert [t.arquivo for t in figuras] == [
        "figuras/acerto_por_condicao.png", "figuras/erros_por_tipo.png", "figuras/custo_por_condicao.png"]
    chaves = [n.chave for t in figuras for n in t.numeros]
    assert len(chaves) == len(set(chaves))
    for t, prefixo in zip(figuras, ("figura_acerto_", "figura_erros_", "figura_custo_"), strict=True):
        conferir_registrados(t, r, prefixo)


def test_subtitulo_de_cada_figura_cabe_numa_linha_do_kit(tmp_path):
    # o kit reserva uma linha para o subtítulo, entre o eixo e o título: quebrado, ele invadiria o título
    raiz = tmp_path / "raiz"
    pasta_rodadas = gerar_rodadas_sinteticas(raiz, semente=7, repeticoes=0)
    numeros_json = raiz / "resultados" / "numeros.json"
    analisar(pasta_rodadas, raiz / "avaliacao" / "revisao_veredictos.csv", numeros_json=numeros_json,
             pasta_tabelas=raiz / "relatorio" / "tabelas")

    for t in textos_das_figuras(numeros.carregar(numeros_json)):
        assert "\n" not in t.subtitulo
        assert len(t.subtitulo) <= MAX_SUBTITULO, t.subtitulo


def test_onde_aparece_do_numero_da_analise_inclui_a_figura_e_sobrevive_a_nova_analise(tmp_path):
    raiz = tmp_path / "raiz"
    pasta_rodadas = gerar_rodadas_sinteticas(raiz, semente=7, repeticoes=0)
    numeros_json = raiz / "resultados" / "numeros.json"

    def analisar_raiz():
        analisar(pasta_rodadas, raiz / "avaliacao" / "revisao_veredictos.csv", numeros_json=numeros_json,
                 pasta_tabelas=raiz / "relatorio" / "tabelas")

    analisar_raiz()
    registrar_figuras(textos_das_figuras(numeros.carregar(numeros_json)), caminho=numeros_json)
    analisar_raiz()  # o 04 roda de novo depois das figuras

    r = numeros.carregar(numeros_json)
    onde = usos(r, "", {})
    assert r["com_rag_acerto_resposta"]["script"] == SCRIPT_04
    assert "figuras/acerto_por_condicao.png" in onde["com_rag_acerto_resposta"]
    assert "figuras/custo_por_condicao.png" in onde["com_rag_acerto_resposta"]
    assert "relatorio/tabelas/resultados_por_condicao.tex" in onde["com_rag_acerto_resposta"]
    assert not [c for c in r if c.startswith("figura_acerto_")]  # nenhuma cópia
    assert onde["figura_custo_razao_tokens"] == ["figuras/custo_por_condicao.png"]


def test_figuras_de_rodadas_sinteticas_nunca_vao_para_uma_copia_do_projeto(tmp_path):
    raiz = tmp_path / "raiz"
    pasta_rodadas = gerar_rodadas_sinteticas(raiz, semente=7, repeticoes=0)
    projeto = tmp_path / "projeto"
    projeto.mkdir()
    (projeto / "pyproject.toml").write_text("", encoding="utf-8")

    with pytest.raises(RaizProibida):
        recusar_no_projeto(pasta_rodadas, projeto / "figuras", passo="as figuras")
    with pytest.raises(RaizProibida):
        recusar_no_projeto(pasta_rodadas, raiz / "figuras", projeto / "resultados" / "numeros.json", passo="as figuras")
    recusar_no_projeto(pasta_rodadas, raiz / "figuras", raiz / "resultados" / "numeros.json", passo="as figuras")


def test_a_fonte_no_rodape_avisa_quando_as_rodadas_sao_sinteticas():
    assert "sintéticas" in fonte_dos_dados(sintetica=True)
    assert "sintéticas" not in fonte_dos_dados(sintetica=False)
    assert not NUMERO_IMPRESSO.search(fonte_dos_dados(sintetica=True) + fonte_dos_dados(sintetica=False))

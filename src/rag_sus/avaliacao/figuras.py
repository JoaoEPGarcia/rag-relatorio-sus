# -*- coding: utf-8 -*-
"""O que cada figura diz: título, subtítulo, rótulos e os números que imprime.

POR QUE ISTO EXISTE. A regra do portfólio vale também para as figuras: todo
número impresso num título ou rótulo sai do registro, por f-string, e fica no
NUMEROS_CANONICOS.md com a figura na coluna "Onde aparece" (ADR 0003). Aqui,
sem matplotlib, sai o texto de cada figura a partir do registro gravado por
scripts/04_analisar.py; o desenho fica em scripts/05_figuras.py.

Um número da análise impresso numa figura não é copiado: a figura declara
que o usa (numeros.declarar_usos), e a entrada continua uma só, do
scripts/04_analisar.py, com a figura em "Onde aparece" mesmo depois de uma
nova análise. Só o número que a própria figura calcula (a razão entre os
tokens, a soma dos erros) vira chave do scripts/05_figuras.py, prefixada pela
figura (`figura_custo_razao_tokens`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rag_sus import numeros
from rag_sus.assistente import CONDICOES
from rag_sus.avaliacao.gabarito import TIPOS_RESPONDIVEIS
from rag_sus.avaliacao.vocabulario import (
    CLASSES_DAS_RESPONDIVEIS,
    CLASSES_DE_ERRO,
    CONCLUSOES,
    NOMES_TIPO,
    SO_NAS_SEM_RESPOSTA,
    chave_por_tipo,
    juntar,
    lado_do_ic,
    mais_frequentes,
    rotulo_condicao,
)
from rag_sus.numeros import Numero, formatar


@dataclass(frozen=True)
class TextosDaFigura:
    arquivo: str  # caminho relativo à raiz do projeto, como a coluna "Onde aparece" cita
    titulo: str
    subtitulo: str
    rotulos: dict[str, str] = field(default_factory=dict)
    numeros: tuple[Numero, ...] = ()  # os números que só a figura calcula, registrados como dela
    usos: tuple[str, ...] = ()  # as chaves do registro que a figura imprime, sem copiá-las
    linhas: tuple[str, ...] = ()  # ordem das categorias no eixo, de cima para baixo
    colunas: tuple[str, ...] = ()  # ordem dos painéis, da esquerda para a direita
    destaque: tuple[str, ...] = ()  # o que sai em DESTAQUE; o resto sai em NEUTRO


class _Impressos:
    """Devolve o texto de uma chave do registro e anota que a figura a imprime."""

    def __init__(self, registro: dict[str, dict], nome: str, arquivo: str):
        self.registro, self.nome, self.arquivo = registro, nome, arquivo
        self.numeros: dict[str, Numero] = {}
        self.usos: list[str] = []

    def __call__(self, chave: str) -> str:
        if chave not in self.registro:
            raise KeyError(f"{chave} não está no registro: rode scripts/04_analisar.py antes das figuras")
        if chave not in self.usos:
            self.usos.append(chave)
        return self.registro[chave]["texto"]

    def novo(self, chave: str, valor, descricao: str, formato: str) -> str:
        """Um número calculado aqui, e não no 04_analisar.py (uma razão, por exemplo): vira chave da figura."""
        nova = f"figura_{self.nome}_{chave}"
        self.numeros[nova] = Numero(nova, valor, f"{descricao}, impresso na figura", formato, (self.arquivo,))
        return formatar(valor, formato)

    def valor(self, chave: str):
        """O valor de uma chave, para decidir o texto, sem imprimi-lo."""
        return self.registro[chave]["valor"]


def _lado_da_diferenca(t: _Impressos, comparacao: str) -> int:
    """+1 se o IC da diferença pareada (com RAG menos a outra) fica acima de zero, −1 se abaixo, 0 se cruza."""
    return lado_do_ic(t.valor(f"{comparacao}_diferenca_inf"), t.valor(f"{comparacao}_diferenca_sup"))


def textos_acerto(registro: dict[str, dict]) -> TextosDaFigura:
    """Acerto da resposta por Condição, com o IC de Wilson; com RAG em destaque."""
    arquivo = "figuras/acerto_por_condicao.png"
    t = _Impressos(registro, "acerto", arquivo)
    com, sem = t("com_rag_acerto_resposta"), t("sem_rag_acerto_resposta")
    lado = _lado_da_diferenca(t, "com_rag_x_sem_rag")
    if lado > 0:
        titulo = f"Com RAG, o assistente acerta {com} das respostas, contra {sem} sem RAG"
    elif lado < 0:
        titulo = f"Sem RAG, o assistente acerta mais: {sem} das respostas, contra {com} com RAG"
    else:
        titulo = f"Com RAG e sem RAG, o acerto não se distingue: {com} contra {sem} das respostas"
    rotulos = {
        c: f"{t(f'{c}_acerto_resposta')} (IC {t(f'{c}_acerto_resposta_inf')} a {t(f'{c}_acerto_resposta_sup')})"
        for c in CONDICOES
    }
    n = t("destaque_n_respondiveis")
    nivel = t("ic_nivel")
    subtitulo = (f"Acerto da resposta nas {n} Perguntas respondíveis, Rodada principal. "
                 f"A linha fina é o intervalo de confiança de Wilson de {nivel}%.")
    return TextosDaFigura(arquivo, titulo, subtitulo, rotulos, tuple(t.numeros.values()), tuple(t.usos),
                          linhas=CONDICOES, destaque=("com_rag",))


def textos_custo(registro: dict[str, dict]) -> TextosDaFigura:
    """Tokens de entrada e latência por Pergunta, por Condição, ao lado do acerto: se cabe no contexto, para que RAG?"""
    arquivo = "figuras/custo_por_condicao.png"
    t = _Impressos(registro, "custo", arquivo)
    rag, cc = t("com_rag_acerto_resposta"), t("contexto_completo_acerto_resposta")
    tokens_rag, tokens_cc = t.valor("com_rag_tokens_entrada_medio"), t.valor("contexto_completo_tokens_entrada_medio")
    razao = max(tokens_rag, tokens_cc) / min(tokens_rag, tokens_cc)
    vezes = t.novo("razao_tokens", razao,
                   "quantas vezes os tokens de entrada médios de uma Condição cabem nos da outra, "
                   "contexto completo × com RAG", "dec0" if razao >= 10 else "dec1")
    cc_le_mais = tokens_cc >= tokens_rag
    lado = _lado_da_diferenca(t, "com_rag_x_contexto_completo")
    if lado > 0:
        titulo = (f"Com RAG, o assistente acerta mais que com o contexto completo, {rag} contra {cc}, "
                  f"e lê {vezes} vezes {'menos' if cc_le_mais else 'mais'} tokens por Pergunta")
    else:
        conectivo = "mas lê" if cc_le_mais else "e ainda lê"
        quanto = f"{vezes} vezes {'mais' if cc_le_mais else 'menos'} tokens por Pergunta"
        if lado < 0:
            titulo = f"O contexto completo acerta mais, {cc} contra {rag} com RAG, {conectivo} {quanto}"
        else:
            # o IC inclui o zero: a mesma leitura neutra do registro (com_rag_x_contexto_completo_conclusao)
            neutra = CONCLUSOES[0][0]
            titulo = (f"Com RAG, {rag}, contra o contexto completo, {cc}: {neutra}, "
                      f"{'mas' if cc_le_mais else 'e'} o contexto completo lê {quanto}")

    rotulos = {"coluna/tokens": "Tokens de entrada por Pergunta (escala logarítmica)",
               "coluna/latencia": "Latência por Pergunta, em segundos"}
    for c in CONDICOES:
        rotulos[c] = f"{rotulo_condicao(c)}\nacerta {t(f'{c}_acerto_resposta')}"
        rotulos[f"{c}/tokens"] = f"média {t(f'{c}_tokens_entrada_medio')}"
        rotulos[f"{c}/latencia"] = f"mediana {t(f'{c}_latencia_mediana_s')} s"
    n = t("gabarito_n_perguntas")
    subtitulo = (f"Cada caixa resume as {n} Perguntas da Rodada principal numa Condição (traço: mediana; "
                 "losango: média). O acerto é o da resposta, nas Perguntas respondíveis.")
    return TextosDaFigura(arquivo, titulo, subtitulo, rotulos, tuple(t.numeros.values()), tuple(t.usos),
                          linhas=CONDICOES, colunas=("tokens", "latencia"), destaque=("com_rag",))


def textos_das_figuras(registro: dict[str, dict]) -> list[TextosDaFigura]:
    """As três figuras, na ordem em que o Relatório de avaliação as apresenta."""
    return [textos_acerto(registro), textos_erros(registro), textos_custo(registro)]


def fonte_dos_dados(sintetica: bool) -> str:
    """O rodapé das figuras; nas Rodadas sintéticas, avisa que os números são inventados."""
    if sintetica:
        return ("Fonte: Rodadas sintéticas de demonstração, com números inventados; "
                "não é resultado do assistente.")
    return ("Fonte: Rodada principal da avaliação do assistente sobre o relatório Gestão Hospitalar no SUS-SP, "
            "com os Veredictos revisados pelo autor.")


def textos_erros(registro: dict[str, dict]) -> TextosDaFigura:
    """Classes de erro por Tipo de pergunta, na Condição com RAG; a classe mais comum em destaque."""
    arquivo = "figuras/erros_por_tipo.png"
    t = _Impressos(registro, "erros", arquivo)
    totais = {slug: t.valor(f"com_rag_erros_{slug}") for slug in CLASSES_DE_ERRO}
    destaque = mais_frequentes(totais)

    if not destaque:
        titulo = "Com RAG, o assistente não errou nenhuma resposta nem citação"
    elif len(destaque) == 1:
        total = t.novo("total", sum(totais.values()), "erros com RAG, somadas todas as Classes de erro", "inteiro")
        titulo = (f"Com RAG, a {CLASSES_DE_ERRO[destaque[0]].nome} é a Classe de erro mais comum: "
                  f"{t(f'com_rag_erros_{destaque[0]}')} dos {total} erros")
    else:
        classes = juntar([f"a {CLASSES_DE_ERRO[s].nome}" for s in destaque])
        titulo = (f"Com RAG, {classes} empatam como Classe de erro mais comum, "
                  f"com {t(f'com_rag_erros_{destaque[0]}')} erros cada")

    def erros_do_tipo(tipo: str) -> int:
        return sum(t.valor(chave_por_tipo(tipo, s)) for s in CLASSES_DAS_RESPONDIVEIS)

    linhas = (*sorted(TIPOS_RESPONDIVEIS, key=erros_do_tipo, reverse=True), "sem_resposta")
    colunas = tuple(sorted(totais, key=totais.get, reverse=True))
    rotulos: dict[str, str] = {}
    for slug in colunas:
        nome = CLASSES_DE_ERRO[slug].nome
        rotulos[f"coluna/{slug}"] = f"{nome[:1].upper()}{nome[1:]} ({t(f'com_rag_erros_{slug}')})"
    for tipo in linhas:
        rotulos[tipo] = f"{NOMES_TIPO[tipo]} ({t(chave_por_tipo(tipo, 'n'))})"
        aplicaveis = (SO_NAS_SEM_RESPOSTA,) if tipo == "sem_resposta" else CLASSES_DAS_RESPONDIVEIS
        for slug in aplicaveis:
            if t.valor(chave_por_tipo(tipo, slug)) > 0:
                rotulos[f"{tipo}/{slug}"] = t(chave_por_tipo(tipo, slug))

    n = t("gabarito_n_perguntas")
    subtitulo = (f"Perguntas com erro nas {n} da Rodada principal com RAG. Entre parênteses, as Perguntas do "
                 "Tipo e os erros da Classe. Resposta inventada só há nas sem resposta; as demais, nas respondíveis.")
    return TextosDaFigura(arquivo, titulo, subtitulo, rotulos, tuple(t.numeros.values()), tuple(t.usos),
                          linhas=linhas, colunas=colunas, destaque=destaque)


SCRIPT = "scripts/05_figuras.py"


def registrar_figuras(figuras: list[TextosDaFigura], caminho: Path | None = None) -> dict[str, str]:
    """Grava os números que só as figuras calculam e declara onde elas imprimem os da análise.

    Os da análise não são copiados: cada figura entra no "Onde aparece" da
    chave de origem, e o uso sobrevive a uma nova execução do 04_analisar.py.
    """
    registrados = numeros.registrar_do_script(SCRIPT, [n for t in figuras for n in t.numeros], caminho=caminho)
    usos: dict[str, list[str]] = {}
    for t in figuras:
        for chave in t.usos:
            usos.setdefault(chave, []).append(t.arquivo)
    numeros.declarar_usos(SCRIPT, usos, caminho=caminho)
    return registrados

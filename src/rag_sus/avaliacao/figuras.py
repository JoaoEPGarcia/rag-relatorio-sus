# -*- coding: utf-8 -*-
"""O que cada figura diz: título, subtítulo, rótulos e os números que imprime.

POR QUE ISTO EXISTE. A regra do portfólio vale também para as figuras: todo
número impresso num título ou rótulo sai do registro, por f-string, e fica no
NUMEROS_CANONICOS.md com a figura na coluna "Onde aparece" (ADR 0003). Aqui,
sem matplotlib, sai o texto de cada figura a partir do registro gravado por
scripts/04_analisar.py; o desenho fica em scripts/05_figuras.py.

Cada número impresso é registrado de novo, com a chave prefixada pela figura
(`figura_acerto_com_rag_acerto_resposta`), pelo scripts/05_figuras.py: a
entrada de origem continua do 04_analisar.py, que a reescreve a cada análise,
e a da figura declara onde aparece. O valor é o mesmo, copiado do registro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rag_sus.assistente import CONDICOES
from rag_sus.avaliacao.estatistica import NIVEL
from rag_sus.avaliacao.gabarito import TIPOS_RESPONDIVEIS
from rag_sus.avaliacao.resultados import CLASSES_DE_ERRO, NOMES_CONDICAO, NOMES_TIPO
from rag_sus.avaliacao.sinteticas import RaizProibida, dentro_de_uma_copia_do_projeto, rodada_sintetica
from rag_sus.numeros import Numero, formatar


@dataclass(frozen=True)
class TextosDaFigura:
    arquivo: str  # caminho relativo à raiz do projeto, como a coluna "Onde aparece" cita
    titulo: str
    subtitulo: str
    rotulos: dict[str, str] = field(default_factory=dict)
    numeros: tuple[Numero, ...] = ()
    linhas: tuple[str, ...] = ()  # ordem das categorias no eixo, de cima para baixo
    colunas: tuple[str, ...] = ()  # ordem dos painéis, da esquerda para a direita
    destaque: tuple[str, ...] = ()  # o que sai em DESTAQUE; o resto sai em NEUTRO


class _Impressos:
    """Devolve o texto de uma chave do registro e anota o número como impresso na figura."""

    def __init__(self, registro: dict[str, dict], nome: str, arquivo: str):
        self.registro, self.nome, self.arquivo = registro, nome, arquivo
        self.numeros: dict[str, Numero] = {}

    def __call__(self, chave: str) -> str:
        if chave not in self.registro:
            raise KeyError(f"{chave} não está no registro: rode scripts/04_analisar.py antes das figuras")
        e = self.registro[chave]
        return self._anotar(chave, e["valor"], e["descricao"], e["formato"])

    def novo(self, chave: str, valor, descricao: str, formato: str) -> str:
        """Um número calculado aqui, e não no 04_analisar.py (uma razão, por exemplo)."""
        return self._anotar(chave, valor, descricao, formato)

    def _anotar(self, chave: str, valor, descricao: str, formato: str) -> str:
        nova = f"figura_{self.nome}_{chave}"
        self.numeros[nova] = Numero(nova, valor, f"{descricao} (na figura {self.arquivo})", formato, (self.arquivo,))
        return formatar(valor, formato)

    def valor(self, chave: str):
        """O valor de uma chave, para decidir o texto, sem imprimi-lo."""
        return self.registro[chave]["valor"]


def _lado_da_diferenca(t: _Impressos, comparacao: str) -> int:
    """+1 se o IC da diferença pareada (com RAG menos a outra) fica acima de zero, −1 se abaixo, 0 se cruza."""
    if t.valor(f"{comparacao}_diferenca_inf") > 0:
        return 1
    if t.valor(f"{comparacao}_diferenca_sup") < 0:
        return -1
    return 0


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
    nivel = t.novo("nivel_ic", round(100 * NIVEL), "nível de confiança dos intervalos, em %", "inteiro")
    subtitulo = (f"Acerto da resposta nas {n} Perguntas respondíveis, Rodada principal. "
                 f"A linha fina é o intervalo de confiança de Wilson de {nivel}%.")
    return TextosDaFigura(arquivo, titulo, subtitulo, rotulos, tuple(t.numeros.values()),
                          linhas=CONDICOES, destaque=("com_rag",))


def _nome_de_abertura(condicao: str) -> str:
    """"contexto completo" -> "Contexto completo"."""
    nome = NOMES_CONDICAO[condicao]
    return nome[:1].upper() + nome[1:]


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
            titulo = f"O contexto completo acerta {cc}, perto dos {rag} com RAG, {conectivo} {quanto}"

    rotulos = {"coluna/tokens": "Tokens de entrada por Pergunta (escala logarítmica)",
               "coluna/latencia": "Latência por Pergunta, em segundos"}
    for c in CONDICOES:
        rotulos[c] = f"{_nome_de_abertura(c)}\nacerta {t(f'{c}_acerto_resposta')}"
        rotulos[f"{c}/tokens"] = f"média {t(f'{c}_tokens_entrada_medio')}"
        rotulos[f"{c}/latencia"] = f"mediana {t(f'{c}_latencia_mediana_s')} s"
    n = t("gabarito_n_perguntas")
    subtitulo = (f"Cada caixa resume as {n} Perguntas da Rodada principal numa Condição (traço: mediana; "
                 "losango: média). O acerto é o da resposta, nas Perguntas respondíveis.")
    return TextosDaFigura(arquivo, titulo, subtitulo, rotulos, tuple(t.numeros.values()),
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


def recusar_sinteticas_no_projeto(pasta_rodadas: Path, *destinos: Path) -> None:
    """Rodadas sintéticas não viram figura nem número dentro de uma cópia do projeto."""
    if rodada_sintetica(Path(pasta_rodadas) / "principal") and any(
        dentro_de_uma_copia_do_projeto(d) for d in destinos
    ):
        raise RaizProibida(
            "as Rodadas sintéticas de demonstração não viram figura nem número numa cópia do projeto: "
            "rode as figuras com RAG_SUS_RAIZ apontando para a raiz temporária"
        )


def _em_lista(nomes: list[str]) -> str:
    """["a x", "a y", "a z"] -> "a x, a y e a z"."""
    return nomes[0] if len(nomes) == 1 else f"{', '.join(nomes[:-1])} e {nomes[-1]}"


def textos_erros(registro: dict[str, dict]) -> TextosDaFigura:
    """Classes de erro por Tipo de pergunta, na Condição com RAG; a classe mais comum em destaque."""
    arquivo = "figuras/erros_por_tipo.png"
    t = _Impressos(registro, "erros", arquivo)
    nome_da_classe = {slug: classe for classe, slug in CLASSES_DE_ERRO.items()}
    totais = {slug: t.valor(f"com_rag_erros_{slug}") for slug in CLASSES_DE_ERRO.values()}
    maior = max(totais.values())
    destaque = tuple(slug for slug, k in totais.items() if k == maior) if maior > 0 else ()

    if not destaque:
        titulo = "Com RAG, o assistente não errou nenhuma resposta nem citação"
    elif len(destaque) == 1:
        total = t.novo("total", sum(totais.values()), "erros com RAG, somadas todas as Classes de erro", "inteiro")
        titulo = (f"Com RAG, a {nome_da_classe[destaque[0]]} é a Classe de erro mais comum: "
                  f"{t(f'com_rag_erros_{destaque[0]}')} dos {total} erros")
    else:
        classes = _em_lista([f"a {nome_da_classe[s]}" for s in destaque])
        titulo = (f"Com RAG, {classes} empatam como Classe de erro mais comum, "
                  f"com {t(f'com_rag_erros_{destaque[0]}')} erros cada")

    def erros_do_tipo(tipo: str) -> int:
        return sum(t.valor(f"com_rag_tipo_{tipo}_{s}") for s in CLASSES_DE_ERRO.values() if s != "resposta_inventada")

    linhas = (*sorted(TIPOS_RESPONDIVEIS, key=erros_do_tipo, reverse=True), "sem_resposta")
    colunas = tuple(sorted(totais, key=totais.get, reverse=True))
    rotulos: dict[str, str] = {}
    for slug in colunas:
        nome = nome_da_classe[slug]
        rotulos[f"coluna/{slug}"] = f"{nome[:1].upper()}{nome[1:]} ({t(f'com_rag_erros_{slug}')})"
    for tipo in linhas:
        rotulos[tipo] = f"{NOMES_TIPO[tipo]} ({t(f'com_rag_tipo_{tipo}_n')})"
        aplicaveis = ("resposta_inventada",) if tipo == "sem_resposta" else (
            s for s in CLASSES_DE_ERRO.values() if s != "resposta_inventada")
        for slug in aplicaveis:
            if t.valor(f"com_rag_tipo_{tipo}_{slug}") > 0:
                rotulos[f"{tipo}/{slug}"] = t(f"com_rag_tipo_{tipo}_{slug}")

    n = t.novo("n_perguntas", sum(t.valor(f"com_rag_tipo_{tipo}_n") for tipo in linhas),
               "Perguntas da Rodada principal com RAG, respondíveis e sem resposta", "inteiro")
    subtitulo = (f"Perguntas com erro, por Classe de erro e Tipo de pergunta, nas {n} Perguntas da Rodada "
                 "principal com RAG. Entre parênteses, quantas Perguntas há do Tipo e quantos erros há na "
                 "Classe. A resposta inventada só existe nas sem resposta; as demais, só nas respondíveis.")
    return TextosDaFigura(arquivo, titulo, subtitulo, rotulos, tuple(t.numeros.values()),
                          linhas=linhas, colunas=colunas, destaque=destaque)

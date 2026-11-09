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

from rag_sus.assistente import CONDICOES
from rag_sus.avaliacao.estatistica import NIVEL
from rag_sus.numeros import Numero, formatar


@dataclass(frozen=True)
class TextosDaFigura:
    arquivo: str  # caminho relativo à raiz do projeto, como a coluna "Onde aparece" cita
    titulo: str
    subtitulo: str
    rotulos: dict[str, str] = field(default_factory=dict)
    numeros: tuple[Numero, ...] = ()


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
    return TextosDaFigura(arquivo, titulo, subtitulo, rotulos, tuple(t.numeros.values()))

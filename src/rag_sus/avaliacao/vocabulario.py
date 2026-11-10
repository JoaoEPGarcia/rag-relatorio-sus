# -*- coding: utf-8 -*-
"""Os nomes e as leituras que a análise e as figuras compartilham.

POR QUE ISTO EXISTE. A análise (resultados.py), os textos das figuras
(figuras.py) e o desenho delas (scripts/05_figuras.py) escrevem os mesmos
nomes de Condição, de Tipo de pergunta e de Classe de erro, e tomam as mesmas
decisões a partir do resultado: qual Classe de erro é a mais frequente (com
empate), o que o IC de uma diferença pareada permite dizer, que chave do
registro guarda cada cruzamento. Um lugar só evita que o README, o Relatório
de avaliação e as figuras digam coisas diferentes sobre o mesmo número.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

NOMES_CONDICAO = {"com_rag": "com RAG", "sem_rag": "sem RAG", "contexto_completo": "contexto completo"}
NOMES_TIPO = {
    "numero_prosa": "Número na prosa",
    "numero_tabela": "Número em tabela",
    "numero_legenda": "Número em legenda",
    "conceito": "Conceito ou método",
    "sintese": "Síntese entre páginas",
    "sem_resposta": "Sem resposta",
}


@dataclass(frozen=True)
class ClasseDeErro:
    nome: str  # como sai de pontuacao.classificar_erro
    nome_en: str  # na seção "In English" do README


# pedaço da chave no registro -> Classe de erro; a ordem é a das colunas e a do desempate
CLASSES_DE_ERRO = {
    "falha_recuperacao": ClasseDeErro("falha de recuperação", "retrieval failure"),
    "falha_leitura": ClasseDeErro("falha de leitura", "reading failure"),
    "abstencao_indevida": ClasseDeErro("abstenção indevida", "unwarranted abstention"),
    "citacao_errada": ClasseDeErro("citação errada", "wrong citation"),
    "resposta_inventada": ClasseDeErro("resposta inventada", "made-up answer"),
}
# A resposta inventada só acontece nas Perguntas sem resposta; as outras Classes, só nas respondíveis.
SO_NAS_SEM_RESPOSTA = "resposta_inventada"
CLASSES_DAS_RESPONDIVEIS = tuple(s for s in CLASSES_DE_ERRO if s != SO_NAS_SEM_RESPOSTA)

# O que o IC da diferença pareada (com RAG menos a outra) permite dizer, por lado do zero.
CONCLUSOES = {
    1: ("com RAG acerta mais", "RAG gets more answers right"),
    -1: ("com RAG acerta menos", "RAG gets fewer answers right"),
    0: ("os dados não distinguem as duas Condições", "the data cannot tell the two conditions apart"),
}


def rotulo_condicao(condicao: str) -> str:
    """"com RAG" -> "Com RAG", para abrir uma linha de tabela ou um rótulo de figura."""
    nome = NOMES_CONDICAO[condicao]
    return nome[:1].upper() + nome[1:]


def juntar(nomes: Sequence[str], e: str = "e") -> str:
    """["a", "b", "c"] -> "a, b e c" (`e="and"` para o inglês)."""
    return nomes[0] if len(nomes) == 1 else f"{', '.join(nomes[:-1])} {e} {nomes[-1]}"


def mais_frequentes(contagem: Mapping[str, int]) -> tuple[str, ...]:
    """As chaves com a maior contagem, todas as empatadas, na ordem de `contagem`; nenhuma se tudo é zero."""
    maior = max(contagem.values(), default=0)
    return tuple(k for k, n in contagem.items() if n == maior) if maior > 0 else ()


def lado_do_ic(inferior: float, superior: float) -> int:
    """+1 se o IC fica todo acima de zero, −1 se todo abaixo, 0 se inclui o zero."""
    if inferior > 0:
        return 1
    if superior < 0:
        return -1
    return 0


def chave_por_tipo(tipo: str, classe: str) -> str:
    """A chave do registro com as respostas de uma Classe de erro num Tipo de pergunta, com RAG."""
    return f"com_rag_tipo_{tipo}_{classe}"

# -*- coding: utf-8 -*-
"""O assistente: monta o prompt de cada Condição e devolve a resposta citada.

POR QUE ISTO EXISTE. As três Condições da avaliação usam o mesmo modelo, o
mesmo esquema de saída e as mesmas regras de resposta; só muda o que o modelo
recebe do Relatório-fonte:

- com RAG: os k Trechos recuperados, cada um marcado com a sua página;
- sem RAG: nada (o modelo responde com o que já sabe, ou se abstém);
- contexto completo: o texto inteiro, página por página, no prompt de
  sistema (lido do cache a partir da segunda Pergunta).

Mantê-las num lugar só garante que a comparação mude uma coisa de cada vez.
O prompt não menciona nenhum fato do Relatório-fonte: na Condição sem RAG,
isso vazaria a resposta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from rag_sus.busca import Embutidor, IndiceDeTrechos, Resultado
from rag_sus.provedores import Metadados, Provedor

Condicao = Literal["com_rag", "sem_rag", "contexto_completo"]
CONDICOES: tuple[Condicao, ...] = ("com_rag", "sem_rag", "contexto_completo")

TITULO = 'o relatório "Gestão Hospitalar no SUS-SP" (2026)'

ESQUEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        "resposta": {"type": "string"},
        "paginas_citadas": {"type": "array", "items": {"type": "integer"}},
        "abstencao": {"type": "boolean"},
    },
    "required": ["resposta", "paginas_citadas", "abstencao"],
    "additionalProperties": False,
}

_REGRAS = """Regras da resposta:
- Responda em português do Brasil, em uma a três frases, direto ao ponto.
- Copie os números exatamente como aparecem no relatório, no formato brasileiro \
(vírgula decimal, ponto de milhar), sem arredondar e sem converter unidades.
- Em "paginas_citadas", ponha o número de cada página de onde tirou a resposta. \
A página é o número que aparece na marcação [página N].
- Se o material não responde à pergunta, marque "abstencao" como true, diga em \
"resposta" que o relatório não trata disso e deixe "paginas_citadas" vazia. \
Não complete com conhecimento de fora do material."""

SISTEMA_COM_RAG = f"""Você responde perguntas sobre {TITULO}, usando só os trechos \
do relatório que vêm junto com cada pergunta.

{_REGRAS}"""

SISTEMA_CONTEXTO_COMPLETO = f"""Você responde perguntas sobre {TITULO}, usando só o \
texto do relatório que vem abaixo, página por página.

{_REGRAS}"""

SISTEMA_SEM_RAG = f"""Você responde perguntas sobre {TITULO}. Você não tem o texto \
do relatório à mão: responda só se souber.

Regras da resposta:
- Responda em português do Brasil, em uma a três frases, direto ao ponto.
- Escreva números no formato brasileiro (vírgula decimal, ponto de milhar).
- Em "paginas_citadas", ponha a página do relatório de onde vem a resposta, se souber; \
se não souber, deixe a lista vazia.
- Se não souber a resposta, marque "abstencao" como true e diga isso em "resposta". \
Não invente números nem páginas."""


@dataclass
class RespostaAssistente:
    condicao: Condicao
    resposta: str
    paginas_citadas: tuple[int, ...]
    abstencao: bool
    paginas_recuperadas: tuple[int, ...] = ()
    trechos_recuperados: tuple[str, ...] = ()
    metadados: Metadados | None = None
    extras: dict = field(default_factory=dict)


def formatar_trechos(resultados: list[Resultado]) -> str:
    blocos = []
    for r in resultados:
        t = r.trecho
        rotulo = {"tabela": "tabela", "legenda": "legenda de figura"}.get(t.tipo, "texto")
        blocos.append(f"[página {t.pagina_impressa} | {rotulo}]\n{t.texto}")
    return "\n\n".join(blocos)


class Assistente:
    def __init__(
        self,
        provedor: Provedor,
        indice: IndiceDeTrechos | None = None,
        embutidor: Embutidor | None = None,
        k: int = 6,
        texto_completo: str | None = None,
    ):
        self.provedor = provedor
        self.indice = indice
        self.embutidor = embutidor
        self.k = k
        self.texto_completo = texto_completo

    def responder(self, pergunta: str, condicao: Condicao = "com_rag") -> RespostaAssistente:
        recuperados: list[Resultado] = []
        if condicao == "com_rag":
            if self.indice is None or self.embutidor is None:
                raise ValueError("a Condição com RAG precisa do índice e do embutidor")
            recuperados = self.indice.buscar(pergunta, self.embutidor, self.k)
            sistema = [{"type": "text", "text": SISTEMA_COM_RAG}]
            mensagem = (
                f"Trechos do relatório:\n\n{formatar_trechos(recuperados)}\n\n"
                f"Pergunta: {pergunta}"
            )
        elif condicao == "contexto_completo":
            if not self.texto_completo:
                raise ValueError("a Condição contexto completo precisa do texto completo")
            sistema = [
                {"type": "text", "text": SISTEMA_CONTEXTO_COMPLETO},
                {"type": "text", "text": f"Texto do relatório:\n\n{self.texto_completo}"},
            ]
            mensagem = f"Pergunta: {pergunta}"
        elif condicao == "sem_rag":
            sistema = [{"type": "text", "text": SISTEMA_SEM_RAG}]
            mensagem = f"Pergunta: {pergunta}"
        else:
            raise ValueError(f"Condição desconhecida: {condicao}")

        saida, meta = self.provedor.gerar_json(sistema, mensagem, ESQUEMA_RESPOSTA)
        return RespostaAssistente(
            condicao=condicao,
            resposta=str(saida.get("resposta", "")).strip(),
            paginas_citadas=tuple(int(p) for p in saida.get("paginas_citadas", [])),
            abstencao=bool(saida.get("abstencao", False)),
            paginas_recuperadas=tuple(IndiceDeTrechos.paginas(recuperados)),
            trechos_recuperados=tuple(r.trecho.id for r in recuperados),
            metadados=meta,
        )

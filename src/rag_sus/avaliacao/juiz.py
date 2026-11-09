# -*- coding: utf-8 -*-
"""O Juiz: decide se uma resposta descritiva coincide com o Gabarito.

POR QUE ISTO EXISTE. Respostas de conceito e de síntese não se conferem por
regra ("o que mede a DEA?"). O Juiz é um modelo que compara a resposta com o
Gabarito e emite um Veredicto com justificativa curta. Ele julga só o
conteúdo; a página citada é conferida à parte, por regra. Todos os Veredictos
do Juiz na Rodada principal passam pela Revisão do autor antes de valer.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag_sus.provedores import Metadados, Provedor

ESQUEMA_VEREDICTO = {
    "type": "object",
    "properties": {
        "acerto": {"type": "boolean"},
        "justificativa": {"type": "string"},
    },
    "required": ["acerto", "justificativa"],
    "additionalProperties": False,
}

SISTEMA_JUIZ = """Você confere respostas de um assistente contra um gabarito conferido \
por uma pessoa. Decida se a resposta do assistente diz o que o gabarito diz.

Critérios:
- Acerto: a resposta contém a informação central do gabarito, com os mesmos números \
quando o gabarito tem números. Pode ter outras palavras e detalhes a mais, desde que \
não contradigam o gabarito.
- Erro: falta a informação central, algum número diverge, ou a resposta contradiz o \
gabarito. Uma resposta que diz não saber, ou que o relatório não trata do assunto, é erro.
- Ignore as páginas citadas: elas são conferidas à parte.

Escreva a justificativa em português, em uma frase."""


@dataclass(frozen=True)
class Veredicto:
    acerto: bool
    justificativa: str
    metadados: Metadados | None = None


class Juiz:
    def __init__(self, provedor: Provedor):
        self.provedor = provedor

    def julgar(self, pergunta: str, gabarito: str, resposta: str) -> Veredicto:
        mensagem = (
            f"Pergunta:\n{pergunta}\n\n"
            f"Gabarito:\n{gabarito}\n\n"
            f"Resposta do assistente:\n{resposta}"
        )
        saida, meta = self.provedor.gerar_json(
            [{"type": "text", "text": SISTEMA_JUIZ}], mensagem, ESQUEMA_VEREDICTO
        )
        return Veredicto(bool(saida["acerto"]), str(saida["justificativa"]).strip(), meta)

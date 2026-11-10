# -*- coding: utf-8 -*-
"""Folha de Revisão dos Veredictos do Juiz em PDF (ticket 10).

POR QUE ISTO EXISTE. Na Rodada principal, todo Veredicto do Juiz precisa da
Revisão do autor antes de valer; a Revisão vence o Juiz. A folha CSV
(avaliacao/revisao_veredictos.csv) tem respostas longas e é ruim de ler.
Esta folha põe, por Condição, cada Pergunta com o Gabarito, a resposta do
assistente, o Veredicto e a justificativa do Juiz. O autor responde no chat
só onde discorda, e o agente preenche `veredicto_revisado`.

Só entram os Veredictos do Juiz. As respostas pontuadas pela regra (todos os
valores do Gabarito presentes) e as abstenções não passam pelo Juiz e não
precisam de Revisão.
"""

from __future__ import annotations

import csv
from pathlib import Path

from rag_sus.assistente import CONDICOES
from rag_sus.avaliacao.folha_do_gabarito import MODELO_DO_KIT, documento_do_kit, escapar
from rag_sus.avaliacao.vocabulario import NOMES_TIPO, rotulo_condicao


def _ler(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _cartao(l: dict, tipo: str) -> str:
    cor = "verdeTexto" if l["veredicto_juiz"] == "certo" else "vermelho"
    return "\n".join([
        rf"\cartao{{{l['id']}}}{{{escapar(NOMES_TIPO.get(tipo, tipo))}}}"
        rf"{{\selo{{{cor}}}{{Juiz: {l['veredicto_juiz']}}}}}",
        rf"\campo{{Pergunta}} {escapar(l['pergunta'])}\par",
        rf"\campo{{Gabarito}} {escapar(l['gabarito'])}\par",
        rf"\campo{{Resposta do assistente}} {escapar(l['resposta'])}\par",
        rf"\campo{{Justificativa do Juiz}} {{\itshape {escapar(l['justificativa_juiz'])}}}\par",
        r"\marcas",
    ])


def gerar_tex(folha_csv: Path, gabarito_csv: Path, modelo_do_kit: Path = MODELO_DO_KIT) -> str:
    linhas = _ler(folha_csv)
    tipos = {g["id"]: g["tipo"] for g in _ler(gabarito_csv)}
    certos = sum(l["veredicto_juiz"] == "certo" for l in linhas)
    macros = {"NumVeredictos": len(linhas), "NumJuizCerto": certos, "NumJuizErrado": len(linhas) - certos}

    secoes = []
    for condicao in CONDICOES:
        da_condicao = [l for l in linhas if l["condicao"] == condicao]
        if not da_condicao:
            continue
        secoes += [r"\clearpage", rf"\section*{{{rotulo_condicao(condicao)}}}"]
        secoes += [_cartao(l, tipos.get(l["id"], "")) for l in da_condicao]

    corpo = [
        r"\section*{Como revisar}",
        r"O Juiz é um modelo que compara a resposta do assistente com o Gabarito e diz se ela está certa. "
        r"Ele só é chamado quando a regra não basta: nas respostas descritivas, e nas numéricas em que a "
        r"regra não achou todos os valores do Gabarito. Para cada cartão, decida se a resposta diz o que o "
        r"Gabarito diz:",
        r"\begin{itemize}[nosep]",
        r"  \item \textbf{certo}: tem a informação central do Gabarito, com os mesmos números quando ele tem "
        r"números; palavras diferentes e detalhes a mais valem, desde que não o contradigam;",
        r"  \item \textbf{errado}: falta a informação central, algum número diverge, a resposta contradiz o "
        r"Gabarito ou diz que o relatório não trata do assunto.",
        r"\end{itemize}",
        r"As páginas citadas não entram aqui: elas são conferidas à parte, por regra. A sua Revisão vence o "
        r"Juiz, e sem ela os resultados não são publicados.",
        "",
        r"\subsection*{Como responder no chat}",
        r"Mande só onde você discorda do Juiz. O que você não citar fica com o Veredicto dele.",
        r"\begin{verbatim}",
        r"Iniciais: ___",
        r"De acordo com o Juiz em todos, exceto:",
        r"com_rag G__ certo: <por que>",
        r"contexto_completo G__ errado: <por que>",
        r"\end{verbatim}",
        "",
        r"\subsection*{O que há nesta folha}",
        r"\NumVeredictos{} Veredictos do Juiz na Rodada principal: \NumJuizCerto{} certos e "
        r"\NumJuizErrado{} errados, segundo ele.",
        *secoes,
    ]
    return documento_do_kit(
        gerado_por="scripts/gerar_folha_dos_veredictos.py a partir de avaliacao/revisao_veredictos.csv",
        rotulo=r"FOLHA DE TRABALHO \textperiodcentered\ REVISÃO DOS VEREDICTOS",
        titulo="Revisão dos Veredictos",
        subtitulo="As respostas que o Juiz julgou na Rodada principal, para conferir contra o Gabarito",
        delimitacao=r"Assistente de perguntas sobre o relatório Gestão Hospitalar no SUS-SP"
                    r" \\ \NumVeredictos{} Veredictos do Juiz",
        macros=macros,
        marcas=r"\faSquare[regular]~de acordo com o Juiz\qquad\faSquare[regular]~discordo",
        corpo=corpo,
        modelo_do_kit=modelo_do_kit,
    )

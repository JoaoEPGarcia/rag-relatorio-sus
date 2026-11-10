# -*- coding: utf-8 -*-
"""Folha de Revisão do Gabarito em PDF, para o autor conferir no Relatório-fonte.

POR QUE ISTO EXISTE. O Gabarito proposto (avaliacao/gabarito.csv) só vale
depois que o autor confere cada linha no PDF do Relatório-fonte (ADR 0002,
ticket 08). Ler 60 linhas de CSV é ruim; esta folha mostra cada Pergunta com
a resposta proposta, os valores, as páginas impressas com link para a página
do arquivo (página impressa + 1, ADR 0004) e os alertas da extração
("ATENÇÃO", "CONFERIR"). O autor responde no chat só as exceções, e o agente
grava a coluna `revisado`.

O visual é o do kit: o preâmbulo e a capa são lidos de estilo/modelo_relatorio.tex
sem edição. As contagens do roteiro são macros calculadas aqui, e não digitadas.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from rag_sus import config
from rag_sus.avaliacao.vocabulario import NOMES_TIPO

MODELO_DO_KIT = config.RAIZ / "estilo" / "modelo_relatorio.tex"
_SEPARADOR = re.compile(r" \| (?=p\. \d|ATENÇÃO:|CONFERIR:)")

_TROCAS = [
    ("\\", r"\textbackslash{}"),
    ("{", r"\{"), ("}", r"\}"),
    ("%", r"\%"), ("&", r"\&"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"),
    ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
    ("|", r"\textbar{}"),
    ("−", "$-$"), ("∙", r"$\cdot$"), ("—", "---"),
    ("η", r"$\eta$"), ("τ", r"$\tau$"), ("θ", r"$\theta$"),
    ("²", r"\textsuperscript{2}"), ("³", r"\textsuperscript{3}"),
]


def escapar(texto: str) -> str:
    """Texto do CSV para o pdfLaTeX, caractere a caractere."""
    mapa = dict(_TROCAS)
    return "".join(mapa.get(c, c) for c in texto)


def _trecho_do_kit(texto: str, inicio: str, fim: str) -> str:
    a = texto.index(inicio)
    b = texto.index(fim, a) + len(fim)
    return texto[a:b]


def _alertas(observacao: str) -> tuple[bool, bool, bool]:
    atencao = "ATENÇÃO" in observacao
    conferir = "CONFERIR" in observacao
    troca = "trocar" in observacao.lower()
    return atencao, conferir, troca


def _link_da_pagina(pdf_fonte: Path, impressa: int) -> str:
    uri = Path(pdf_fonte).resolve().as_uri().replace("%", r"\%")
    return rf"\href{{{uri}\#page={impressa + 1}}}{{p.~{impressa}}} {{\color{{tinta3}}(arquivo: {impressa + 1})}}"


def _origem(observacao: str) -> str:
    itens = []
    # O separador entre as partes é " | " seguido de "p. N:" ou de um alerta; dentro
    # de uma citação de tabela, o "|" separa células e não abre parte nova.
    for parte in (p.strip() for p in _SEPARADOR.split(observacao) if p.strip()):
        for rotulo, cor in (("ATENÇÃO:", "vermelho"), ("CONFERIR:", "azulTexto")):
            if parte.startswith(rotulo):
                parte = rf"{{\color{{{cor}}}\lato\bfseries {rotulo[:-1]}.}} " + escapar(parte[len(rotulo):].strip())
                break
        else:
            parte = escapar(parte)
        itens.append(rf"  \item {parte}")
    return "\\begin{itemize}[nosep, leftmargin=1.2em]\n" + "\n".join(itens) + "\n\\end{itemize}"


def _cartao(l: dict, pdf_fonte: Path) -> str:
    atencao, conferir, troca = _alertas(l["observacao"])
    selos = []
    if troca:
        selos.append(r"\selo{vermelho}{candidata a troca}")
    elif atencao:
        selos.append(r"\selo{vermelho}{atenção}")
    if conferir:
        selos.append(r"\selo{azulTexto}{conferir}")
    partes = [
        rf"\cartao{{{l['id']}}}{{{escapar(NOMES_TIPO[l['tipo']])}}}{{{' '.join(selos)}}}",
        rf"\campo{{Pergunta}} {escapar(l['pergunta'])}\par",
        rf"\campo{{Resposta proposta}} {escapar(l['resposta'])}\par",
    ]
    if l["valores"].strip():
        valores = r" \textperiodcentered\ ".join(escapar(v.strip()) for v in l["valores"].split(";"))
        partes.append(rf"\campo{{Valores exigidos}} {valores}\par")
    if l["paginas"].strip():
        paginas = ", ".join(_link_da_pagina(pdf_fonte, int(p)) for p in l["paginas"].split(";"))
        partes.append(rf"\campo{{Páginas impressas}} {paginas}\par")
    if l["observacao"].strip():
        partes.append(r"\campo{De onde veio}" + "\n" + _origem(l["observacao"]))
    partes.append(r"\marcas")
    return "\n".join(partes)


def gerar_tex(gabarito_csv: Path, pdf_fonte: Path, modelo_do_kit: Path = MODELO_DO_KIT) -> str:
    with open(gabarito_csv, encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    kit = Path(modelo_do_kit).read_text(encoding="utf-8")
    preambulo = _trecho_do_kit(kit, r"\documentclass", "% FIM DO PREÂMBULO DO KIT\n"
                               "% ══════════════════════════════════════════════════════════════════════")
    capa = _trecho_do_kit(kit, r"\begin{titlepage}", r"\end{titlepage}")

    respondiveis = [l for l in linhas if l["tipo"] != "sem_resposta"]
    sem_resposta = [l for l in linhas if l["tipo"] == "sem_resposta"]
    alertas = {l["id"]: _alertas(l["observacao"]) for l in linhas}
    ids_atencao = [i for i, (a, _, _) in alertas.items() if a]
    ids_conferir = [i for i, (_, c, _) in alertas.items() if c]
    ids_troca = [i for i, (_, _, t) in alertas.items() if t]

    def lista(ids):
        return ", ".join(ids) if ids else "nenhuma"

    macros = {
        "NumPerguntas": len(linhas), "NumRespondiveis": len(respondiveis), "NumSemResposta": len(sem_resposta),
        "NumAtencao": len(ids_atencao), "NumConferir": len(ids_conferir), "NumTroca": len(ids_troca),
    }
    corpo = [
        "% GERADO por scripts/gerar_folha_do_gabarito.py a partir de avaliacao/gabarito.csv. Não edite à mão.",
        preambulo,
        "",
        r"\newcommand{\RotuloCapa}{FOLHA DE TRABALHO \textperiodcentered\ REVISÃO DO GABARITO}",
        r"\newcommand{\TituloRelatorio}{Revisão do Gabarito}",
        r"\newcommand{\SubtituloRelatorio}{As Perguntas propostas, para conferir no PDF do Relatório-fonte}",
        r"\newcommand{\DelimitacaoRelatorio}{Assistente de perguntas sobre o relatório Gestão Hospitalar no SUS-SP"
        r" \\ \NumPerguntas{} Perguntas: \NumRespondiveis{} respondíveis e \NumSemResposta{} sem resposta}",
        r"\newcommand{\AutorNome}{João Eduardo Pastori Garcia}",
        r"\newcommand{\AutorPapel}{Estatístico responsável}",
        r"\newcommand{\AutorLinkedIn}{https://www.linkedin.com/in/joao-eduardo-garcia/}",
        r"\newcommand{\AutorGitHub}{https://github.com/JoaoEPGarcia}",
        r"\newcommand{\LocalCapa}{São Paulo -- SP}",
        r"\newcommand{\DataCapa}{\ifcase\month\or Janeiro\or Fevereiro\or Março\or Abril\or Maio\or Junho\or"
        r" Julho\or Agosto\or Setembro\or Outubro\or Novembro\or Dezembro\fi\ de \number\year}",
        "",
        *(rf"\newcommand{{\{k}}}{{{v}}}" for k, v in macros.items()),
        "",
        r"\newcommand{\selo}[2]{{\lato\small\bfseries\color{#1}\MakeUppercase{#2}}}",
        r"\newcommand{\cartao}[3]{\needspace{12\baselineskip}\subsection*{#1 \textperiodcentered\ "
        r"{\mdseries\color{tinta2}#2}\hfill #3}}",
        r"\newcommand{\campo}[1]{\noindent{\lato\small\bfseries\color{tinta2}#1.}~}",
        r"\newcommand{\marcas}{\par\smallskip\noindent{\lato\small\color{tinta2}"
        r"\faSquare[regular]~ok\qquad\faSquare[regular]~corrigir\qquad\faSquare[regular]~trocar}"
        r"\par\medskip\noindent{\color{zebraclara}\rule{\linewidth}{0.8pt}}\par}",
        "",
        r"\begin{document}",
        capa.replace(r"\faDatabase", r"\faFilePdf").replace(r"\faChartLine", r"\faSearch")
            .replace(r"\faCalculator", r"\faClipboardCheck").replace(r"\faCalendarDay", r"\faComments"),
        "",
        r"\section*{Como revisar}",
        r"Abra o PDF do Relatório-fonte ao lado desta folha. Para cada Pergunta, confira quatro coisas:",
        r"\begin{enumerate}[nosep]",
        r"  \item a Pergunta é inequívoca e tem uma resposta só;",
        r"  \item a resposta proposta diz o que o relatório diz;",
        r"  \item os valores exigidos aparecem no relatório exatamente assim (a regra de pontuação exige todos);",
        r"  \item as páginas impressas listam todas as páginas em que a resposta aparece.",
        r"\end{enumerate}",
        r"Nas Perguntas sem resposta, confirme que o relatório não trata do tema. O número da página é o "
        r"impresso no rodapé; entre parênteses vai a posição no arquivo, e o link abre o PDF nela.",
        "",
        r"\subsection*{Como responder no chat}",
        r"Mande só as exceções. O que você não citar fica aprovado como está.",
        r"\begin{verbatim}",
        r"Iniciais: ___",
        r"Todas ok, exceto:",
        r"G__ resposta: <o texto certo>",
        r"G__ valores: <os valores certos, separados por ;>",
        r"G__ páginas: <as páginas impressas, separadas por ;>",
        r"G__ pergunta: <a redação nova>",
        r"G__ trocar",
        r"S__ está no relatório: p. __",
        r"\end{verbatim}",
        r"Para uma Pergunta trocada, eu proponho outra do mesmo Tipo, e ela volta para você conferir.",
        "",
        r"\subsection*{Roteiro: comece por estas}",
        r"\begin{itemize}[nosep]",
        rf"  \item {{\color{{vermelho}}\lato\bfseries Candidatas a troca}} (\NumTroca): {lista(ids_troca)}.",
        rf"  \item {{\color{{vermelho}}\lato\bfseries Atenção}} (\NumAtencao): dúvidas da extração; "
        rf"{lista(ids_atencao)}.",
        rf"  \item {{\color{{azulTexto}}\lato\bfseries Conferir}} (\NumConferir): os mesmos valores aparecem em "
        rf"outras páginas; {lista(ids_conferir)}.",
        r"\end{itemize}",
        "",
        r"\clearpage",
        r"\section*{As Perguntas respondíveis}",
        *(_cartao(l, pdf_fonte) for l in respondiveis),
        r"\clearpage",
        r"\section*{As Perguntas sem resposta}",
        *(_cartao(l, pdf_fonte) for l in sem_resposta),
        r"\end{document}",
        "",
    ]
    return "\n".join(corpo)

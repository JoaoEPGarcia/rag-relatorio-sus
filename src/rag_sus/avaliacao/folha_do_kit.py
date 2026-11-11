# -*- coding: utf-8 -*-
"""O esqueleto comum às folhas de Revisão em PDF, no visual do kit.

POR QUE ISTO EXISTE. As duas folhas de trabalho (Revisão do Gabarito e
Revisão dos Veredictos do Juiz) usam o mesmo preâmbulo e a mesma capa do kit,
lidos de estilo/modelo_relatorio.tex sem edição, e escapam o texto dos CSVs
do mesmo jeito. Um lugar só evita que as duas se afastem.

O kit é código, como o README.base.md: vem sempre da cópia do projeto
(config.PROJETO), e não de config.RAIZ, que pode ser uma raiz temporária sem
estilo/.

`escapar` não é o `documentos.texto_tex`: aquele escapa só o que os números
formatados do registro trazem (\\, %, $, o sinal de menos e "< "); este
escapa o texto livre dos CSVs, com chaves, &, #, _, | e letras gregas.
"""

from __future__ import annotations

from pathlib import Path

from rag_sus import config

MODELO_DO_KIT = config.PROJETO / "estilo" / "modelo_relatorio.tex"

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


def documento_do_kit(*, gerado_por: str, rotulo: str, titulo: str, subtitulo: str, delimitacao: str,
                     macros: dict, marcas: str, corpo: list[str], modelo_do_kit: Path = MODELO_DO_KIT) -> str:
    """Uma folha de trabalho com o preâmbulo e a capa do kit, lidos sem edição.

    `marcas` é a linha de caixas de marcar no fim de cada cartão; `corpo` vem
    depois da capa. As contagens entram como macros, calculadas por quem chama.
    """
    kit = Path(modelo_do_kit).read_text(encoding="utf-8")
    preambulo = _trecho_do_kit(kit, r"\documentclass", "% FIM DO PREÂMBULO DO KIT\n"
                               "% ══════════════════════════════════════════════════════════════════════")
    capa = _trecho_do_kit(kit, r"\begin{titlepage}", r"\end{titlepage}")
    return "\n".join([
        f"% GERADO por {gerado_por}. Não edite à mão.",
        preambulo,
        "",
        rf"\newcommand{{\RotuloCapa}}{{{rotulo}}}",
        rf"\newcommand{{\TituloRelatorio}}{{{titulo}}}",
        rf"\newcommand{{\SubtituloRelatorio}}{{{subtitulo}}}",
        rf"\newcommand{{\DelimitacaoRelatorio}}{{{delimitacao}}}",
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
        r"\newcommand{\marcas}{\par\smallskip\noindent{\lato\small\color{tinta2}" + marcas + "}"
        r"\par\medskip\noindent{\color{zebraclara}\rule{\linewidth}{0.8pt}}\par}",
        "",
        r"\begin{document}",
        capa.replace(r"\faDatabase", r"\faFilePdf").replace(r"\faChartLine", r"\faSearch")
            .replace(r"\faCalculator", r"\faClipboardCheck").replace(r"\faCalendarDay", r"\faComments"),
        "",
        *corpo,
        r"\end{document}",
        "",
    ])

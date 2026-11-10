# -*- coding: utf-8 -*-
"""Passo 5: as figuras do Relatório de avaliação e do README (não chama o modelo).

POR QUE ISTO EXISTE. Três figuras no estilo do portfólio, cada uma com o
título afirmando o achado: o Acerto da resposta por Condição, com o IC de
Wilson; as Classes de erro por Tipo de pergunta, com RAG; e os tokens de
entrada e a latência por Pergunta, por Condição, ao lado do acerto. O texto
de cada figura sai de rag_sus.avaliacao.figuras, a partir do registro que o
scripts/04_analisar.py grava; aqui fica só o desenho. Cada número da análise
impresso numa figura ganha a figura em "Onde aparece", sem cópia no registro;
os que só a figura calcula (a razão dos tokens, a soma dos erros) são
registrados como deste script.

Uso (depois do scripts/04_analisar.py):
  uv run python scripts/05_figuras.py
Sobre as Rodadas sintéticas (raiz temporária, nunca as figuras reais):
  RAG_SUS_RAIZ=/tmp/rag-sus-demo uv run python scripts/05_figuras.py
"""

import math
import sys
import textwrap
from pathlib import Path

# o kit copiado, relativo ao script (e não a config.RAIZ, que pode ser uma raiz temporária)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "estilo"))

import matplotlib.pyplot as plt  # noqa: E402
from estilo_portfolio import (  # noqa: E402
    DESTAQUE,
    GRAY_60,
    GRAY_70,
    GRAY_80,
    NEUTRO,
    TAM_ROTULO_EIXO,
    cor_de_texto,
    destacar,
    eixo_no_zero,
    fonte,
    misturar,
    rotular_ponta,
    sem_grade,
    set_sus_style,
    titulo,
)
from matplotlib.ticker import FuncFormatter, NullLocator  # noqa: E402

from rag_sus import config, numeros  # noqa: E402
from rag_sus.assistente import CONDICOES  # noqa: E402
from rag_sus.avaliacao.figuras import (  # noqa: E402
    TextosDaFigura,
    fonte_dos_dados,
    registrar_figuras,
    textos_das_figuras,
)
from rag_sus.avaliacao.rodada import carregar_linhas  # noqa: E402
from rag_sus.avaliacao.sinteticas import RaizProibida, recusar_no_projeto, rodada_sintetica  # noqa: E402
from rag_sus.avaliacao.vocabulario import chave_por_tipo, rotulo_condicao  # noqa: E402

# Folga no alto do eixo, em unidades de categoria, para o nome do painel caber dentro dele.
FOLGA_DO_NOME_DO_PAINEL = 0.7


def _cabecalho(ax, texto: str, subtitulo: str, largura: int) -> None:
    """O título e o subtítulo, pela função do kit, sem mexer no que ela posiciona.

    Só o título se quebra em linhas (ele cresce para cima a partir do pad do
    kit); o subtítulo cabe numa linha, que é o espaço que o kit reserva para ele.
    """
    titulo(ax, textwrap.fill(texto, largura), subtitulo)


def _nome_do_painel(ax, texto: str) -> None:
    """O nome do painel, dentro do eixo, no alto: o espaço acima do eixo é do título e do subtítulo do kit."""
    ax.annotate(texto, xy=(0, 1), xycoords="axes fraction", xytext=(0, -2), textcoords="offset points",
                ha="left", va="top", fontsize=TAM_ROTULO_EIXO, color=GRAY_70)


def _eixo_de_categorias(ax, linhas: tuple[str, ...], rotulos: dict[str, str], destaque: tuple[str, ...]):
    """Categorias de cima para baixo; a que está em destaque, na cor de texto do destaque (o peso é o regular)."""
    y = {c: len(linhas) - 1 - i for i, c in enumerate(linhas)}
    ax.set_yticks([y[c] for c in linhas], [rotulos[c] for c in linhas])
    for marca, c in zip(ax.get_yticklabels(), linhas, strict=True):
        if c in destaque:
            marca.set_color(cor_de_texto(DESTAQUE))
    return y


def _salvar(fig, t: TextosDaFigura) -> Path:
    destino = config.RAIZ / t.arquivo
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino)  # tight e 150 dpi vêm do tema do kit
    plt.close(fig)
    return destino


def _porcentagem(v, _pos) -> str:
    return f"{numeros.formatar(round(100 * v), 'inteiro')}%"


def figura_acerto(t: TextosDaFigura, registro: dict[str, dict], rodape: str) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4.2))
    y = _eixo_de_categorias(ax, t.linhas, {c: rotulo_condicao(c) for c in t.linhas}, t.destaque)
    cores = destacar(t.linhas, t.destaque)
    for c in t.linhas:
        valor = registro[f"{c}_acerto_resposta"]["valor"]
        inf, sup = registro[f"{c}_acerto_resposta_inf"]["valor"], registro[f"{c}_acerto_resposta_sup"]["valor"]
        ax.barh(y[c], valor, height=0.56, color=cores[c], zorder=2)
        ax.plot([inf, sup], [y[c], y[c]], color=GRAY_80, linewidth=1.6, zorder=3, solid_capstyle="butt")
        ax.plot([inf, sup], [y[c], y[c]], linestyle="none", marker="|", markersize=11, color=GRAY_80, zorder=3)
        em_destaque = c in t.destaque
        rotular_ponta(ax, sup, y[c], t.rotulos[c], cor=DESTAQUE if em_destaque else GRAY_60, negrito=em_destaque)
    eixo_no_zero(ax, "x", topo=1.0)
    ax.xaxis.set_major_formatter(FuncFormatter(_porcentagem))
    ax.set_xlabel("Acerto da resposta")
    sem_grade(ax)
    _cabecalho(ax, t.titulo, t.subtitulo, largura=72)
    fonte(ax, rodape)
    return _salvar(fig, t)


def figura_erros(t: TextosDaFigura, registro: dict[str, dict], rodape: str) -> Path:
    fig, eixos = plt.subplots(1, len(t.colunas), figsize=(12, 4.8), sharex=True, sharey=True)
    nomes = {c: t.rotulos[c] for c in t.linhas}
    y = _eixo_de_categorias(eixos[0], t.linhas, nomes, ())
    maior = max(registro[chave_por_tipo(tipo, slug)]["valor"]
                for tipo in t.linhas for slug in t.colunas if chave_por_tipo(tipo, slug) in registro)
    for ax, slug in zip(eixos, t.colunas, strict=True):
        cor = DESTAQUE if slug in t.destaque else NEUTRO
        for tipo in t.linhas:
            if f"{tipo}/{slug}" not in t.rotulos:
                continue
            valor = registro[chave_por_tipo(tipo, slug)]["valor"]
            ax.barh(y[tipo], valor, height=0.6, color=cor, zorder=2)
            rotular_ponta(ax, valor, y[tipo], t.rotulos[f"{tipo}/{slug}"],
                          cor=cor if slug in t.destaque else GRAY_60, negrito=slug in t.destaque, dx=4.0)
        _nome_do_painel(ax, t.rotulos[f"coluna/{slug}"])
        sem_grade(ax)
        ax.set_xticks([])
        eixo_no_zero(ax, "x", topo=max(maior, 1) * 1.35)
    eixos[0].set_ylim(-0.6, len(t.linhas) - 0.4 + FOLGA_DO_NOME_DO_PAINEL)
    _cabecalho(eixos[0], t.titulo, t.subtitulo, largura=82)
    fig.subplots_adjust(wspace=0.12)
    fonte(eixos[0], rodape)
    return _salvar(fig, t)


def figura_custo(t: TextosDaFigura, linhas_por_condicao: dict[str, list[dict]], rodape: str) -> Path:
    fig, (ax_tokens, ax_latencia) = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    y = _eixo_de_categorias(ax_tokens, t.linhas, t.rotulos, t.destaque)
    cores = destacar(t.linhas, t.destaque)
    campos = {"tokens": (ax_tokens, "tokens_entrada"), "latencia": (ax_latencia, "latencia_s")}
    for coluna, (ax, campo) in campos.items():
        for c in t.linhas:
            valores = [l[campo] for l in linhas_por_condicao[c] if l.get(campo) is not None]
            cor = cores[c]
            ax.boxplot(
                valores, positions=[y[c]], orientation="horizontal", widths=0.5, patch_artist=True,
                showmeans=True, showfliers=True, manage_ticks=False,
                boxprops={"facecolor": misturar(cor, 0.72), "edgecolor": cor, "linewidth": 1.4},
                medianprops={"color": cor_de_texto(cor), "linewidth": 2.2},
                whiskerprops={"color": cor, "linewidth": 1.4}, capprops={"color": cor, "linewidth": 1.4},
                meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": cor_de_texto(cor),
                           "markersize": 6},
                flierprops={"marker": "o", "markerfacecolor": "white", "markeredgecolor": cor, "markersize": 4},
            )
            em_destaque = c in t.destaque
            rotular_ponta(ax, max(valores), y[c], t.rotulos[f"{c}/{coluna}"],
                          cor=DESTAQUE if em_destaque else GRAY_60, negrito=em_destaque, dx=8.0)
        ax.set_xlabel(t.rotulos[f"coluna/{coluna}"])
        sem_grade(ax)
    ax_tokens.set_ylim(-0.6, len(t.linhas) - 0.4)
    ax_tokens.set_xscale("log")
    menor = min(l["tokens_entrada"] for ls in linhas_por_condicao.values() for l in ls if l.get("tokens_entrada"))
    ax_tokens.set_xlim(left=10 ** math.floor(math.log10(menor)))  # começa numa potência de dez, com marca
    ax_tokens.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: numeros.formatar(v, "inteiro")))
    ax_tokens.xaxis.set_minor_locator(NullLocator())
    eixo_no_zero(ax_latencia, "x")
    ax_latencia.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: numeros.formatar(v, "inteiro")))
    _cabecalho(ax_tokens, t.titulo, t.subtitulo, largura=82)
    fig.subplots_adjust(wspace=0.35)
    fonte(ax_tokens, rodape)
    return _salvar(fig, t)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        recusar_no_projeto(config.RODADAS, config.FIGURAS, config.NUMEROS, passo="as figuras")
        registro = numeros.carregar()
        acerto, erros, custo = textos_das_figuras(registro)
    except (RaizProibida, KeyError) as erro:
        print(f"Figuras paradas: {erro.args[0]}")
        return 1
    principal = config.RODADAS / "principal"
    linhas = {c: carregar_linhas(principal / f"{c}.jsonl") for c in CONDICOES}
    if not all(linhas.values()):
        print(f"Figuras paradas: falta a Rodada principal em {principal}")
        return 1

    set_sus_style()  # antes da primeira figura
    rodape = fonte_dos_dados(rodada_sintetica(principal))
    gravadas = [figura_acerto(acerto, registro, rodape), figura_erros(erros, registro, rodape),
                figura_custo(custo, linhas, rodape)]
    registrados = registrar_figuras([acerto, erros, custo])
    for caminho, t in zip(gravadas, (acerto, erros, custo), strict=True):
        print(f"{caminho}: {t.titulo}")
    usados = len({chave for t in (acerto, erros, custo) for chave in t.usos})
    print(f"{len(registrados)} números das figuras e {usados} usos de números da análise -> {config.NUMEROS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

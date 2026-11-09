# -*- coding: utf-8 -*-
"""Kit de estilo do portfólio: o visual das figuras em matplotlib.

    from estilo_portfolio import set_sus_style, AZUL, DESTAQUE, NEUTRO
    set_sus_style()

    python estilo_portfolio.py --validar

Versão enxuta do `analises/estilo_sus_paulista.py` do projeto de gestão
hospitalar. Os hexadecimais, a escala neutra, a tipografia e os auxiliares
de desenho são os mesmos. Saiu tudo o que era específico das redes
hospitalares (mapa de redes, boxplot padrão, curvas de densidade, bolinhas
de tabela, apelidos de paletas antigas) e a troca automática da cor de
texto: aqui o rótulo colorido passa por `cor_de_texto()`, de forma
explícita.

O que mudou de significado em relação ao projeto de origem:
  · `CATEGORICA` (o ciclo de cor) começa no AZUL, que é o destaque
    principal da capa. No projeto, a ordem era a das quatro redes;
  · `CORES_EXEMPLO` substitui `CORES_REDE`: é só um modelo de mapa,
    para trocar pelo mapa das categorias de cada projeto.

Regra que vale em todo projeto: a cor segue a entidade, nunca a posição.
O mapa de cores é fixo e escrito uma vez; um filtro que tire categorias do
gráfico não repinta as que ficam.

Este módulo não escolhe o tipo de gráfico, não escreve o título e não
decide o que a figura afirma. Isso é do gerador (ver GUIA_ESTILO.md).
"""
from __future__ import annotations

import itertools
import locale
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

# ══════════════════════════════════════════════════════════════════════════
# TIPOGRAFIA: Lato, registrada a partir do arquivo, e não suposta
# ══════════════════════════════════════════════════════════════════════════
# A Lato desta máquina veio com o pacote `lato` do MiKTeX e não está
# instalada no Windows. Registrar o .ttf direto no gerenciador de fontes do
# matplotlib dispensa instalação de sistema. Se nada for achado, a figura
# sai na fonte de recuo e `set_sus_style()` AVISA na tela.
_DIRS_LATO = [
    Path.home() / "AppData/Local/Programs/MiKTeX/fonts/truetype/typoland/lato",
    Path("C:/Program Files/MiKTeX/fonts/truetype/typoland/lato"),
    Path("C:/Windows/Fonts"),
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
    Path("/usr/share/fonts/truetype/lato"),          # Linux (fonts-lato)
]
# Só os pesos usados. Registrar a família inteira faz algumas versões do
# matplotlib escolherem "Hairline" para o peso normal.
_PESOS_LATO = ("Regular", "Bold", "Italic", "BoldItalic", "Semibold", "Black")

FAMILIA: str | None = None
_AVISO_FONTE = ""


def _registrar_lato() -> None:
    """Põe os arquivos da Lato no gerenciador de fontes do matplotlib."""
    global FAMILIA, _AVISO_FONTE
    if FAMILIA is not None:
        return
    from matplotlib import font_manager as fm

    achados = 0
    for d in _DIRS_LATO:
        if not d.is_dir():
            continue
        for arq in sorted(d.glob("Lato-*.ttf")):
            if arq.stem.split("-")[-1] not in _PESOS_LATO:
                continue
            try:
                fm.fontManager.addfont(str(arq))
                achados += 1
            except Exception:
                pass
        if achados:
            break
    if achados:
        FAMILIA = "Lato"
    else:
        FAMILIA = "DejaVu Sans"
        _AVISO_FONTE = (
            "AVISO: a fonte Lato nao foi achada em nenhuma das arvores "
            f"conhecidas. As figuras saem em {FAMILIA}. Instale o pacote "
            "`lato` do MiKTeX (mpm --install lato) e regenere.")


# ══════════════════════════════════════════════════════════════════════════
# A BASE: branco e o quase-preto. Não há preto puro em lugar nenhum.
# ══════════════════════════════════════════════════════════════════════════
BRANCO = "#ffffff"
QUASE_PRETO = "#0A0310"
GERAL = QUASE_PRETO          # o conjunto agregado ("Geral", "Todos")


def misturar(cor: str, branco: float) -> str:
    """A cor aberta para o branco, como hexadecimal SÓLIDO.

    Substitui o `alpha`: `misturar(c, 0.82)` é o pixel que `alpha=0.18`
    daria sobre fundo branco, só que opaco. Não escurece onde duas faixas
    se cruzam e sai igual no PDF, na tela e na impressão. `branco` é a
    fração de branco: 0 devolve a cor cheia e 1 devolve branco.
    """
    from matplotlib.colors import to_hex, to_rgb
    r, g, b = to_rgb(cor)
    f = float(branco)
    return to_hex((r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f))


def escurecer(cor: str, preto: float) -> str:
    """A cor fechada para o QUASE_PRETO (e não para o preto puro)."""
    from matplotlib.colors import to_hex, to_rgb
    r, g, b = to_rgb(cor)
    kr, kg, kb = to_rgb(QUASE_PRETO)
    f = float(preto)
    return to_hex((r + (kr - r) * f, g + (kg - g) * f, b + (kb - b) * f))


# ══════════════════════════════════════════════════════════════════════════
# A PALETA CATEGÓRICA: ColorBrewer Set1, hexa a hexa
# ══════════════════════════════════════════════════════════════════════════
VERMELHO = "#e41a1c"
AZUL = "#377eb8"
VERDE = "#4daf4a"
ROXO = "#984ea3"
# As quatro extras, nesta ordem de preferência. O AMARELO cru tem contraste
# de 1,07:1 contra o branco: serve para área, nunca para linha ou texto.
LARANJA = "#ff7f00"
AMARELO = "#ffff33"
MARROM = "#a65628"
ROSA = "#f781bf"
EXTRAS = [LARANJA, AMARELO, MARROM, ROSA]

# O ciclo de cor de quem não nomeia a categoria. Sem o amarelo.
CATEGORICA = [AZUL, VERMELHO, VERDE, ROXO, LARANJA, MARROM, ROSA]

# Papéis. São os mesmos do projeto de origem: a distribuição de uma
# variável só sai em AZUL, a série que a figura aponta sai em VERMELHO.
# Os dois nunca podem ser o mesmo valor.
COR_BARRA = AZUL
DESTAQUE = VERMELHO
COR_REFERENCIA = VERMELHO     # linha de média ou de meta sobre o dado

# ── EXEMPLO DE MAPA DE CORES: substitua pelo do projeto ───────────────────
# O mapa é escrito UMA vez, aqui ou no topo do gerador, e toda figura o lê.
# Quatro categorias no máximo com cor própria; o que passar disso vai para
# o neutro ou para small multiples.
CORES_EXEMPLO = {
    "Grupo A": AZUL,
    "Grupo B": VERDE,
    "Grupo C": VERMELHO,
    "Grupo D": ROXO,
    "Total": GERAL,
}
# A segunda codificação da identidade, para impressão em preto e branco e
# para a ressalva de protanopia (azul contra roxo; ver `RESSALVAS`).
MARCADORES = ["o", "s", "D", "^", "v", "X"]

# ══════════════════════════════════════════════════════════════════════════
# A ESCALA NEUTRA: o próprio #0A0310 aberto para o branco
# ══════════════════════════════════════════════════════════════════════════
# O cinza da grade e o quase-preto do conjunto são a mesma cor em
# intensidades diferentes: quem vê a figura não aprende uma segunda família.
GRAY_10 = misturar(QUASE_PRETO, 0.95)   # zona de fundo (faixa sombreada)
GRAY_20 = misturar(QUASE_PRETO, 0.90)   # grade, eixo de baixo
GRAY_30 = misturar(QUASE_PRETO, 0.80)   # série de fundo mais apagada
GRAY_40 = misturar(QUASE_PRETO, 0.66)   # série de contexto, atrás da focal
GRAY_50 = misturar(QUASE_PRETO, 0.48)
GRAY_60 = misturar(QUASE_PRETO, 0.34)   # nota de rodapé, linha de média
GRAY_70 = misturar(QUASE_PRETO, 0.22)   # eixo, rótulo, anotação (#403a45)
GRAY_80 = misturar(QUASE_PRETO, 0.12)   # mediana, limite de controle
GRAY_90 = misturar(QUASE_PRETO, 0.03)   # título

TINTA = GRAY_90
TINTA_SECUNDARIA = GRAY_70
GRADE = GRAY_20
NEUTRO = GRAY_40
NEUTRO_CLARO = GRAY_20

# ══════════════════════════════════════════════════════════════════════════
# GRADIENTE: só para MAGNITUDE, nunca para identidade
# ══════════════════════════════════════════════════════════════════════════
# A divergente de onze tons (formato RdYlBu). O vermelho daqui não é a
# categoria vermelha: é a posição na escala.
GRADIENTE = [
    "#a50026", "#d73027", "#f46d43", "#fdae61", "#fee090",
    "#ffffbf",
    "#e0f3f8", "#abd9e9", "#74add1", "#4575b4", "#313695",
]
# A sequencial é a metade fria, que é monótona em luminosidade (a escala
# inteira sobe e desce e não codifica magnitude). Sem o amarelo do meio.
SEQUENCIAL = GRADIENTE[6:]


def mapa_sequencial():
    """Colormap contínuo para magnitude (mapa de calor, coroplético)."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("port_seq", SEQUENCIAL)


def mapa_divergente():
    """Colormap para desvio em torno de um ponto médio com significado."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("port_div", GRADIENTE)


# ══════════════════════════════════════════════════════════════════════════
# UM TAMANHO E UM PESO POR PAPEL DE TEXTO
# ══════════════════════════════════════════════════════════════════════════
# Título em negrito, todo o resto regular. Quem escreve `fontsize=` à mão
# no gerador está criando uma segunda política.
BASE_TIPOGRAFICA = 12.0
TAM_TITULO = BASE_TIPOGRAFICA * 1.20        # 14,4
TAM_SUBTITULO = BASE_TIPOGRAFICA * 0.95     # 11,4
TAM_ROTULO_EIXO = BASE_TIPOGRAFICA * 0.90   # 10,8
TAM_MARCA_EIXO = BASE_TIPOGRAFICA * 0.85    # 10,2
TAM_LEGENDA = BASE_TIPOGRAFICA * 0.85       # 10,2
TAM_ANOTACAO = BASE_TIPOGRAFICA * 0.85      # 10,2  valor AO LADO da marca
TAM_DENTRO_DA_MARCA = BASE_TIPOGRAFICA * 0.75   # 9,0  valor SOBRE a marca
TAM_NOTA = BASE_TIPOGRAFICA * 0.75          # 9,0  rodapé e fonte
PESO_TITULO = "bold"
PESO_DEMAIS = "normal"


# ══════════════════════════════════════════════════════════════════════════
# O TEMA
# ══════════════════════════════════════════════════════════════════════════
_LOCAIS_BR = ("pt_BR.UTF-8", "pt_BR", "Portuguese_Brazil.1252",
              "Portuguese_Brazil", "ptb")


def _grafia_de_numero() -> None:
    """Marca de eixo com vírgula decimal, por padrão (só `LC_NUMERIC`).

    ⚠ Com a locale brasileira, todo inteiro acima de mil ganha separador
    de milhar, e isso inclui o ANO ("2.015"). Eixo de ano chama
    `eixo_ano(ax)`.
    """
    for cand in _LOCAIS_BR:
        try:
            locale.setlocale(locale.LC_NUMERIC, cand)
            return
        except locale.Error:
            continue
    plt.rcParams["axes.formatter.use_locale"] = False
    print("  [estilo] nenhuma locale pt_BR nesta máquina: a marca de eixo "
          "sai com PONTO decimal. Use eixo_virgula(ax).")


def set_sus_style(base: float = BASE_TIPOGRAFICA, grade: bool = True) -> None:
    """Aplica o tema a toda figura criada daqui para a frente.

    `base` é o corpo do texto; o piso é 12, porque a figura é impressa em
    página de PDF. `grade` liga a grade horizontal tracejada; a figura que
    não se lê por valor absoluto chama `sem_grade(ax)`.
    """
    _registrar_lato()
    matplotlib.use("Agg")
    plt.rcParams.update({
        # tipografia: Lato, e nunca preto puro
        "font.family": FAMILIA,
        "font.size": base,
        "axes.titlesize": base * 1.20,
        "axes.titleweight": PESO_TITULO,
        "axes.titlelocation": "left",
        "axes.titlecolor": GRAY_90,
        "axes.labelsize": base * 0.90,
        "axes.labelweight": PESO_DEMAIS,
        "axes.labelcolor": GRAY_70,
        "xtick.labelsize": base * 0.85,
        "ytick.labelsize": base * 0.85,
        # o que estiver entre cifrões também sai em Lato
        "mathtext.fontset": "custom",
        "mathtext.rm": FAMILIA,
        "mathtext.it": f"{FAMILIA}:italic",
        "mathtext.bf": f"{FAMILIA}:bold",
        "mathtext.default": "regular",
        "xtick.color": GRAY_70,
        "ytick.color": GRAY_70,
        "xtick.labelcolor": GRAY_70,
        "ytick.labelcolor": GRAY_70,
        "text.color": GRAY_70,
        "figure.titlesize": base * 1.25,
        "figure.titleweight": "bold",
        # grade: só horizontal, tracejada, atrás do dado
        "axes.grid": grade,
        "axes.grid.axis": "y",
        "grid.color": GRAY_20,
        "grid.linewidth": 0.7,
        "grid.linestyle": (0, (4, 4)),
        "axes.axisbelow": True,
        # moldura: só a linha de baixo
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.spines.bottom": True,
        "axes.edgecolor": GRAY_20,
        "axes.linewidth": 0.8,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        # legenda: existe, mas o rótulo direto vem antes
        "legend.frameon": False,
        "legend.fontsize": base * 0.85,
        "legend.title_fontsize": base * 0.85,
        "legend.labelcolor": GRAY_70,
        # marcas
        "lines.linewidth": 2.0,
        "lines.markersize": 6,
        "patch.linewidth": 0,
        # superfície
        "figure.facecolor": BRANCO,
        "axes.facecolor": BRANCO,
        "savefig.facecolor": BRANCO,
        "savefig.bbox": "tight",
        "savefig.dpi": 150,
        "axes.prop_cycle": plt.cycler(color=CATEGORICA),
        "axes.formatter.use_locale": True,
    })
    _grafia_de_numero()
    if _AVISO_FONTE:
        print(_AVISO_FONTE)


# ══════════════════════════════════════════════════════════════════════════
# AUXILIARES DE DESENHO
# ══════════════════════════════════════════════════════════════════════════
def titulo(ax, texto: str, subtitulo: str | None = None) -> None:
    """Título que AFIRMA o achado, com subtítulo opcional embaixo.

    O subtítulo leva período, unidade e definição da métrica.
    """
    ax.set_title(texto, pad=30 if subtitulo else 12)
    if subtitulo:
        ax.annotate(subtitulo, xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 9), textcoords="offset points",
                    ha="left", va="bottom", fontsize=TAM_SUBTITULO,
                    color=GRAY_70)


def fonte(ax, texto: str) -> None:
    """A fonte dos dados, no rodapé da figura.

    Caminho de arquivo não entra: o rastro de auditoria vive no script e
    no NUMEROS_CANONICOS.md, e não na página.
    """
    ax.figure.text(0.0, -0.02, texto, ha="left", va="top",
                   fontsize=plt.rcParams["font.size"] * 0.75, color=GRAY_60)


def rotular_ponta(ax, x, y, texto: str, cor: str = GRAY_70,
                  dx: float = 6.0, negrito: bool = True, **kw) -> None:
    """Rótulo direto no FIM da linha, no lugar da legenda.

    A cor passa por `cor_de_texto()`: a linha fica na cor cheia e o texto
    sai no mesmo matiz escurecido até ser legível (4,5:1 contra o branco).
    """
    ax.annotate(texto, (x, y), xytext=(dx, 0), textcoords="offset points",
                va="center", ha="left", color=cor_de_texto(cor),
                fontweight="bold" if negrito else "normal",
                fontsize=plt.rcParams["font.size"] * 0.85,
                annotation_clip=False, **kw)


def eixo_virgula(ax, eixo: str = "both", casas: int | None = None) -> None:
    """Marca de eixo com VÍRGULA decimal, independente da locale.

    `casas` fixa o número de casas decimais; sem ele, sai o mínimo
    necessário para cada marca.
    """
    from matplotlib.ticker import FuncFormatter

    def _fmt(v, _pos):
        s = ("%.10g" % v) if casas is None else f"{v:.{casas}f}"
        return s.replace(".", ",")

    if eixo in ("x", "both"):
        ax.xaxis.set_major_formatter(FuncFormatter(_fmt))
    if eixo in ("y", "both"):
        ax.yaxis.set_major_formatter(FuncFormatter(_fmt))


def eixo_ano(ax, eixo: str = "x") -> None:
    """Marca de eixo de ANO, sem separador de milhar ("2015", e não "2.015")."""
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    def _fmt(v, _pos):
        return "%d" % round(v)

    alvo = ax.xaxis if eixo == "x" else ax.yaxis
    alvo.set_major_locator(MaxNLocator(integer=True))
    alvo.set_major_formatter(FuncFormatter(_fmt))


def eixo_no_zero(ax, eixo: str = "y", topo: float | None = None) -> None:
    """Força o eixo a começar em zero. Obrigatório em gráfico de barra."""
    if eixo == "y":
        _, hi = ax.get_ylim()
        ax.set_ylim(0, topo if topo is not None else hi)
    else:
        _, hi = ax.get_xlim()
        ax.set_xlim(0, topo if topo is not None else hi)


def sem_grade(ax) -> None:
    """Desliga a grade, para a figura que não se lê por valor absoluto."""
    ax.grid(False)


def destacar(categorias, foco, cor: str = DESTAQUE,
             fundo: str = NEUTRO) -> dict:
    """Uma cor só na categoria que importa; o resto no neutro."""
    focos = {foco} if isinstance(foco, str) else set(foco)
    return {c: (cor if c in focos else fundo) for c in categorias}


def texto_sobre(fundo: str) -> str:
    """Branco ou quase-preto, o que se ler melhor SOBRE aquele fundo.

    Para número escrito dentro de barra ou célula de mapa de calor. Aceita
    hexadecimal ou a tupla RGBA que o colormap devolve.
    """
    from matplotlib.colors import to_hex
    h = fundo if isinstance(fundo, str) else to_hex(fundo)
    return BRANCO if _contraste(h, BRANCO) >= _contraste(h, GRAY_90) else GRAY_90


# ══════════════════════════════════════════════════════════════════════════
# COR DE TEXTO: a cor cheia escurecida só até ser legível
# ══════════════════════════════════════════════════════════════════════════
def cor_de_texto(cor: str, piso: float = 4.5) -> str:
    """O mesmo matiz, escurecido em passos de 2% até `piso` contra o branco.

    A cor cheia continua em todo preenchimento, linha e marcador; o TEXTO
    escrito nessa cor usa esta versão. O quanto escurecer é calculado, e
    não escolhido a olho. Uma cor que já passa no piso volta intacta.
    """
    passo = 0.0
    while passo <= 1.0:
        cand = escurecer(cor, passo)
        if _contraste(cand, BRANCO) >= piso:
            return cand
        passo += 0.02
    return QUASE_PRETO


# ══════════════════════════════════════════════════════════════════════════
# O VALIDADOR DE PALETA: a parte de cor é computável, então compute
# ══════════════════════════════════════════════════════════════════════════
def _srgb_para_linear(c):
    import numpy as np
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _hex_para_rgb(h: str):
    import numpy as np
    from matplotlib.colors import to_hex
    h = to_hex(h).lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def _para_lab(h: str):
    """sRGB -> CIELAB, D65."""
    import numpy as np
    rgb = _srgb_para_linear(_hex_para_rgb(h))
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    t = (M @ rgb) / np.array([0.95047, 1.0, 1.08883])
    d = 6.0 / 29.0
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d ** 2) + 4.0 / 29.0)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def _deltae(a: str, b: str) -> float:
    import numpy as np
    return float(np.linalg.norm(_para_lab(a) - _para_lab(b)))


def _simular_cvd(h: str, tipo: str) -> str:
    """Viénot, Brettel e Mollon (1999), a simulação padrão de dicromacia."""
    import numpy as np
    from matplotlib.colors import to_hex
    M = {
        "protanopia": np.array([[0.0, 1.05118294, -0.05116099],
                                [0.0, 1.0, 0.0],
                                [0.0, 0.0, 1.0]]),
        "deuteranopia": np.array([[1.0, 0.0, 0.0],
                                  [0.9513092, 0.0, 0.04866992],
                                  [0.0, 0.0, 1.0]]),
        "tritanopia": np.array([[1.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0],
                                [-0.86744736, 1.86727089, 0.0]]),
    }[tipo]
    LMS = np.array([[0.31399022, 0.63951294, 0.04649755],
                    [0.15537241, 0.75789446, 0.08670142],
                    [0.01775239, 0.10944209, 0.87256922]])
    rgb2 = np.clip(np.linalg.inv(LMS) @ (M @ (LMS @ _srgb_para_linear(
        _hex_para_rgb(h)))), 0, 1)
    srgb = np.where(rgb2 <= 0.0031308, rgb2 * 12.92,
                    1.055 * rgb2 ** (1 / 2.4) - 0.055)
    return to_hex(np.clip(srgb, 0, 1))


def _contraste(a: str, b: str) -> float:
    """Razão de contraste WCAG entre duas cores."""
    import numpy as np

    def lum(h):
        return float(np.dot([0.2126, 0.7152, 0.0722],
                            _srgb_para_linear(_hex_para_rgb(h))))
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


# Ressalvas DECLARADAS da paleta padrão. A checagem continua rodando com o
# mesmo limiar e o valor medido aparece na tela; ela só não derruba o
# portão. Ressalva não é limiar baixado. O número fica fora deste
# comentário de propósito: número que sai rodando não apodrece.
RESSALVAS = {
    "protanopia": (
        "azul x roxo abaixo do piso; mitigação: MARCADORES, a segunda "
        "codificação, sempre que os dois forem linha ou ponto no mesmo quadro"),
    "contraste contra o fundo branco": (
        "verde abaixo de 3,0:1; mitigação: cor_de_texto() para texto e "
        "área grande para preenchimento"),
}


def validar_paleta(cores: dict | None = None, verbose: bool = True) -> bool:
    """Bateria de checagens sobre TODOS os pares. Devolve se passou.

    Sem argumento, mede as quatro principais da Set1 e aplica as `RESSALVAS` declaradas. Com um mapa próprio
    (`{"nome": "#hex"}`), mede esse mapa, e aí nenhuma ressalva vale.
    """
    import numpy as np

    if cores is None:
        mapa = {"azul": AZUL, "verde": VERDE, "vermelho": VERMELHO,
                "roxo": ROXO}
        ressalvas = RESSALVAS
    else:
        mapa = dict(cores)
        ressalvas = {}
    nomes, hexas = list(mapa), list(mapa.values())
    linhas, reprovas = [], []

    def registrar(rotulo, detalhe, passou):
        if not passou and rotulo in ressalvas:
            linhas.append((rotulo, f"{detalhe}  << {ressalvas[rotulo]}", None))
            return
        if not passou:
            reprovas.append(rotulo)
        linhas.append((rotulo, detalhe, passou))

    def pior_par(dist):
        pior, par = 1e9, None
        for a, b in itertools.combinations(range(len(hexas)), 2):
            d = dist(hexas[a], hexas[b])
            if d < pior:
                pior, par = d, (nomes[a], nomes[b])
        return pior, par

    labs = [_para_lab(c) for c in hexas]
    Ls = [lab[0] / 100.0 for lab in labs]
    registrar("faixa de luminosidade",
              "L de " + ", ".join(f"{x:.2f}" for x in Ls),
              all(0.20 <= x <= 0.85 for x in Ls))
    cromas = [float(np.hypot(lab[1], lab[2])) / 100.0 for lab in labs]
    registrar("piso de croma", "C de " + ", ".join(f"{c:.2f}" for c in cromas),
              all(c >= 0.10 for c in cromas))

    if len(hexas) >= 2:
        for tipo in ("deuteranopia", "protanopia", "tritanopia"):
            d, par = pior_par(lambda a, b, t=tipo: _deltae(
                _simular_cvd(a, t), _simular_cvd(b, t)))
            registrar(tipo, f"pior par {par[0]} x {par[1]}, deltaE {d:.1f}",
                      d >= 10.0)
        d, par = pior_par(_deltae)
        registrar("piso de visão normal",
                  f"pior par {par[0]} x {par[1]}, deltaE {d:.1f}", d >= 15.0)

    cs = [_contraste(c, BRANCO) for c in hexas]
    registrar("contraste contra o fundo branco",
              ", ".join(f"{n} {c:.1f}:1" for n, c in zip(nomes, cs)),
              all(c >= 3.0 for c in cs))
    ct = [_contraste(cor_de_texto(c), BRANCO) for c in hexas]
    registrar("rótulo legível (cor_de_texto)",
              ", ".join(f"{n} {c:.1f}:1" for n, c in zip(nomes, ct)),
              all(c >= 4.5 for c in ct))

    pior, quem = min((_deltae(GERAL, c), n) for n, c in zip(nomes, hexas))
    registrar("o conjunto separado das categorias",
              f"mais próximo: {quem}, deltaE {pior:.1f}", pior >= 15.0)

    Lseq = [_para_lab(c)[0] for c in SEQUENCIAL]
    registrar("rampa sequencial monótona",
              "L de " + ", ".join(f"{x:.0f}" for x in Lseq),
              all(Lseq[i] > Lseq[i + 1] for i in range(len(Lseq) - 1)))

    ok = not reprovas
    if verbose:
        print("\nA paleta medida:\n")
        for n, c in zip(nomes, hexas):
            print(f"    {n:<16} {c}   texto {cor_de_texto(c)}")
        print(f"    {'conjunto':<16} {GERAL}\n")
        for rot, det, p in linhas:
            marca = "RESSALVA" if p is None else ("PASSA" if p else "FALHA")
            print(f"    {marca:<9}{rot:<36} {det}")
        print("\n    " + ("as checagens de portão passaram." if ok else
                          "HÁ CHECAGEM REPROVADA: " + ", ".join(reprovas)))
        print()
    return ok


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if "--validar" in sys.argv:
        set_sus_style()
        print(f"fonte registrada: {FAMILIA}")
        sys.exit(0 if validar_paleta() else 1)
    print(__doc__)

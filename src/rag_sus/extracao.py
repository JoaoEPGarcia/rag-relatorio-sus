# -*- coding: utf-8 -*-
"""Extração do texto do Relatório-fonte, página a página, em blocos classificados.

POR QUE ISTO EXISTE. A extração bruta do PDF mistura tudo: o corpo, os títulos,
as legendas, as colunas das tabelas uma depois da outra e o número do rodapé.
Para a quebra em Trechos funcionar, cada linha precisa saber o que é. O
Relatório-fonte foi composto em LaTeX com um padrão estável, e é dele que as
regras abaixo dependem (medido em 09/11/2026):

- corpo em Libertine 10,9 pt; parágrafo novo começa recuado (x0 ≈ 102 contra
  margem ≈ 85);
- títulos em Libertine negrito: 14,3 pt (capítulo) e 12,0 pt (seção);
- legendas em 10,0 pt, começando por "Figura N:" ou "Tabela N:";
- notas sob tabela em 9,0 pt; rótulos de painel "(a) ..." em 9,0 pt;
- rodapé: só o número da página impressa, que é a página do PDF menos um
  (a capa não tem número; ver docs/adr/0004).

A tolerância horizontal de 1,5 pt existe porque o texto justificado do LaTeX
tem espaços estreitos: com a tolerância padrão (3 pt), o pdfplumber cola as
palavras ("doSUSnoestadodeSãoPaulo").

Se o Relatório-fonte mudar de diagramação, estas regras precisam ser revistas;
os testes em tests/test_extracao.py descrevem o que cada uma faz.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from rag_sus.modelos import Bloco, Pagina

TOLERANCIA_X = 1.5
TAMANHO_CAPITULO = 14.0
TAMANHO_SECAO = 11.5
TAMANHO_LEGENDA = 10.0
TAMANHO_NOTA = 9.5  # abaixo disto: nota de tabela ou rótulo de painel
RECUO_MINIMO = 8.0  # pt além da margem para contar como início de parágrafo

_INICIO_LEGENDA = re.compile(r"^(Figura|Tabela)\s+[A-Z]?\.?\d+[a-z]?\s*:")
_ROTULO_PAINEL = re.compile(r"^\([a-z]\)\s")
_PONTILHADO_DO_SUMARIO = re.compile(r"(\s*\.){3,}\s*\d*\s*$")
_TEM_LETRA_OU_DIGITO = re.compile(r"[^\W_]")


def pagina_impressa(pagina_pdf: int) -> int:
    """Página impressa no rodapé a partir da posição no PDF (ADR 0004)."""
    return pagina_pdf - 1


def normalizar(texto: str) -> str:
    """NFKC desfaz as ligaduras ("ﬁ" -> "fi") e as letras matemáticas do Apêndice D."""
    return unicodedata.normalize("NFKC", texto)


@dataclass(frozen=True)
class Linha:
    texto: str
    tamanho: float
    negrito: bool
    x0: float
    top: float
    fonte_tabela: bool = False  # Lato: corpo de tabela


def juntar_linhas(linhas: list[str]) -> str:
    """Junta as linhas de um parágrafo, desfazendo a hifenização de fim de linha.

    "fi-" + "lantrópicos" vira "filantrópicos". Só se junta sem hífen quando a
    linha seguinte começa por minúscula, para não estragar "R$" nem siglas.
    """
    texto = ""
    for linha in (l.strip() for l in linhas):
        if not linha:
            continue
        if not texto:
            texto = linha
        elif texto.endswith("-") and linha[:1].islower():
            texto = texto[:-1] + linha
        else:
            texto = f"{texto} {linha}"
    return texto


_TEM_DIGITO = re.compile(r"\d")


def serializar_tabela(linhas: list[list[str | None]], legenda: str = "") -> str:
    """Escreve uma tabela linha a linha, cada célula com o nome da sua coluna.

    Cada linha vira "rótulo: coluna 2: valor; coluna 3: valor", de modo que
    "63,2%" chegue ao Trecho junto com "Filantrópico" e com "taxa de ocupação".
    Três formas do Relatório-fonte pedem cuidado:

    - cabeçalho em duas linhas, quando a primeira começa vazia (grupo de
      colunas acima): os nomes se juntam por coluna ("TMP" + "(dias)");
    - linha de grupo, com uma célula só ("OSS"): entra no rótulo das linhas
      seguintes ("OSS — 5718368");
    - rótulo vazio ("" + "média"): herda o da linha de cima, e uma célula de
      texto sob cabeçalho vazio entra no rótulo ("Direta, média").

    Se a linha tem mais células que o cabeçalho (o pdfplumber partiu uma
    célula), os valores saem em ordem, e o cabeçalho vai uma vez no topo.
    """
    limpas = [[juntar_linhas((c or "").split("\n")) for c in linha] for linha in linhas]
    limpas = [l for l in limpas if any(l)]
    saida: list[str] = [legenda] if legenda else []
    if not limpas:
        return "\n".join(saida)

    n_cabecalho = 1
    if (
        len(limpas) > 1
        and not limpas[0][0]
        and len(limpas[1]) == len(limpas[0])
        and not any(_TEM_DIGITO.search(c) for c in limpas[1])
    ):
        n_cabecalho = 2
    cabecalho = [
        " ".join(l[k] for l in limpas[:n_cabecalho] if k < len(l) and l[k]).strip()
        for k in range(len(limpas[0]))
    ]
    corpo = limpas[n_cabecalho:]
    if not corpo:
        saida.append(" | ".join(c for c in cabecalho if c))
        return "\n".join(saida)

    linhas_saida: list[str] = []
    desalinhada = False
    grupo = ""
    rotulo_anterior = ""
    for linha in corpo:
        preenchidas = [c for c in linha if c]
        if len(preenchidas) == 1 and linha[0] and len(linha) > 1:
            grupo = linha[0]
            continue

        rotulo = linha[0] or rotulo_anterior
        rotulo_anterior = rotulo
        partes_rotulo = [rotulo] if rotulo else []

        if len(linha) != len(cabecalho):
            desalinhada = True
            valores = " | ".join(c for c in linha[1:] if c)
            linhas_saida.append(_com_grupo(grupo, ", ".join(partes_rotulo)) + f": {valores}")
            continue

        partes = []
        for nome, valor in zip(cabecalho[1:], linha[1:], strict=True):
            if not valor:
                continue
            if not nome and not _TEM_DIGITO.search(valor):
                partes_rotulo.append(valor)  # "mediana" sob cabeçalho vazio
            else:
                partes.append(f"{nome}: {valor}" if nome else valor)
        rotulo_final = _com_grupo(grupo, ", ".join(partes_rotulo))
        corpo_linha = "; ".join(partes)
        if rotulo_final and corpo_linha:
            linhas_saida.append(f"{rotulo_final}: {corpo_linha}")
        else:
            linhas_saida.append(rotulo_final or corpo_linha)

    if desalinhada:
        saida.append("Colunas: " + " | ".join(c for c in cabecalho if c))
    saida.extend(linhas_saida)
    return "\n".join(saida)


def _com_grupo(grupo: str, rotulo: str) -> str:
    return f"{grupo} — {rotulo}" if grupo and rotulo else (grupo or rotulo)


@dataclass
class EstadoSecao:
    """O título em vigor atravessa páginas: a seção 1.4 continua na página seguinte."""

    capitulo: str = ""
    secao: str = ""

    @property
    def rotulo(self) -> str:
        if self.capitulo and self.secao:
            return f"{self.capitulo} > {self.secao}"
        return self.capitulo or self.secao


def classificar_linhas(
    linhas: list[Linha], estado: EstadoSecao, margem: float | None = None
) -> list[tuple[float, Bloco]]:
    """Agrupa as linhas de uma página em blocos de parágrafo e de legenda.

    Devolve (posição vertical, bloco) para que as tabelas, extraídas à parte,
    possam ser intercaladas na ordem de leitura. Atualiza `estado` quando
    encontra um título. As linhas de tabela já devem ter sido retiradas.
    """
    if margem is None:
        corpo = [l.x0 for l in linhas if abs(l.tamanho - 10.9) < 0.3]
        margem = min(corpo) if corpo else (min((l.x0 for l in linhas), default=0.0))

    blocos: list[tuple[float, Bloco]] = []
    atual: list[str] = []
    tipo_atual: str | None = None
    topo_atual = 0.0
    titulo: list[str] = []
    tamanho_titulo = 0.0

    def fechar_bloco() -> None:
        nonlocal atual, tipo_atual
        if atual and tipo_atual:
            texto = juntar_linhas(atual)
            if texto:
                blocos.append((topo_atual, Bloco(tipo_atual, texto, estado.rotulo)))
        atual, tipo_atual = [], None

    def fechar_titulo() -> None:
        nonlocal titulo
        if not titulo:
            return
        texto = juntar_linhas(titulo)
        if tamanho_titulo >= TAMANHO_CAPITULO:
            estado.capitulo, estado.secao = texto, ""
        else:
            estado.secao = texto
        titulo = []

    for linha in linhas:
        texto = _PONTILHADO_DO_SUMARIO.sub("", linha.texto).strip()
        if not _TEM_LETRA_OU_DIGITO.search(texto):
            continue  # "∙ ∙ ∙": ícones de sim/não soltos numa linha própria

        e_titulo = linha.negrito and linha.tamanho >= TAMANHO_SECAO and not linha.fonte_tabela
        if e_titulo:
            fechar_bloco()
            if titulo and abs(linha.tamanho - tamanho_titulo) > 0.3:
                fechar_titulo()
            titulo.append(texto)
            tamanho_titulo = linha.tamanho
            continue
        fechar_titulo()

        if linha.tamanho < TAMANHO_NOTA and _ROTULO_PAINEL.match(texto) and len(texto.split()) <= 8:
            continue  # "(a) Mortalidade geral": rótulo de painel, sem conteúdo próprio

        if _INICIO_LEGENDA.match(texto) and abs(linha.tamanho - TAMANHO_LEGENDA) < 0.3:
            fechar_bloco()
            tipo_atual, topo_atual = "legenda", linha.top
            atual.append(texto)
            continue

        if tipo_atual == "legenda" and abs(linha.tamanho - TAMANHO_LEGENDA) < 0.3:
            atual.append(texto)
            continue

        comeca_paragrafo = (
            tipo_atual != "paragrafo"
            or linha.x0 > margem + RECUO_MINIMO
        )
        if comeca_paragrafo:
            fechar_bloco()
            tipo_atual, topo_atual = "paragrafo", linha.top
        atual.append(texto)

    fechar_bloco()
    fechar_titulo()
    return blocos


def anexar_legendas_de_tabela(blocos: list[tuple[float, Bloco]]) -> list[Bloco]:
    """Põe a legenda "Tabela N: ..." como primeira linha do bloco da tabela seguinte.

    A legenda de tabela diz do que a tabela trata; separada dela, a tabela
    vira uma lista de números sem assunto. Legenda de figura fica como está.
    """
    ordenados = [b for _, b in sorted(blocos, key=lambda par: par[0])]
    saida: list[Bloco] = []
    for bloco in ordenados:
        anterior = saida[-1] if saida else None
        if (
            bloco.tipo == "tabela"
            and anterior is not None
            and anterior.tipo == "legenda"
            and anterior.texto.startswith("Tabela")
            and not bloco.texto.startswith("Tabela")
        ):
            saida[-1] = Bloco("tabela", f"{anterior.texto}\n{bloco.texto}", bloco.secao)
        else:
            saida.append(bloco)
    return saida


# --------------------------------------------------------------------------
# Leitura do PDF (a única parte que toca no arquivo)
# --------------------------------------------------------------------------


def extrair_paginas(caminho_pdf: Path | str) -> list[Pagina]:
    """Lê o Relatório-fonte e devolve uma Página por página do PDF, sem a capa."""
    import pdfplumber

    estado = EstadoSecao()
    paginas: list[Pagina] = []
    with pdfplumber.open(str(caminho_pdf)) as pdf:
        for indice, pagina_pdf in enumerate(pdf.pages, start=1):
            if indice == 1:
                continue  # capa: sem número impresso, sem conteúdo para perguntas
            paginas.append(_extrair_pagina(pagina_pdf, indice, estado))
    return marcar_continuacoes(paginas)


_LEGENDA_DE_TABELA = re.compile(r"^(Tabela\s+[A-Z]?\.?\d+[a-z]?)\s*:\s*(.*)$")


def marcar_continuacoes(paginas: list[Pagina]) -> list[Pagina]:
    """Dá a legenda à tabela que continua na página seguinte.

    Quando uma página abre com uma tabela sem legenda e a página anterior
    termina numa tabela com legenda, é a mesma tabela que atravessou a
    página (Tabelas A.1 e A.2). Sem isso, o Trecho da continuação seria uma
    lista de hospitais sem dizer de que lista se trata.
    """
    saida: list[Pagina] = []
    for pagina in paginas:
        anterior = saida[-1] if saida else None
        blocos = list(pagina.blocos)
        tabelas_anteriores = [b for b in anterior.blocos if b.tipo == "tabela"] if anterior else []
        if tabelas_anteriores and blocos:
            ultimo, primeiro = tabelas_anteriores[-1], blocos[0]
            casamento = _LEGENDA_DE_TABELA.match(ultimo.texto.split("\n", 1)[0])
            if (
                primeiro.tipo == "tabela"
                and casamento
                and not primeiro.texto.startswith("Tabela")
            ):
                rotulo, resto = casamento.groups()
                legenda = f"{rotulo} (continuação): {resto}"
                blocos[0] = Bloco("tabela", f"{legenda}\n{primeiro.texto}", primeiro.secao)
                pagina = Pagina(pagina.pagina_pdf, pagina.pagina_impressa, tuple(blocos))
        saida.append(pagina)
    return saida


def _extrair_pagina(pagina_pdf, indice: int, estado: EstadoSecao) -> Pagina:
    tabelas = _tabelas_da_pagina(pagina_pdf)
    caixas = [bbox for bbox, _ in tabelas]

    linhas: list[Linha] = []
    for bruta in pagina_pdf.extract_text_lines(x_tolerance=TOLERANCIA_X, return_chars=True):
        meio = (bruta["top"] + bruta["bottom"]) / 2
        if any(x0 - 2 <= bruta["x0"] and bruta["x1"] <= x1 + 2 and top - 2 <= meio <= bottom + 2
               for x0, top, x1, bottom in caixas):
            continue
        linhas.append(_linha(bruta))

    linhas = _sem_rodape(linhas, pagina_impressa(indice))

    secao_no_inicio = EstadoSecao(estado.capitulo, estado.secao)
    blocos = classificar_linhas(linhas, estado)

    # A seção de uma tabela é a que vale na altura dela: se um título vem
    # depois da tabela na mesma página, a tabela pertence à seção anterior.
    for (_x0, top, _x1, _bottom), texto in tabelas:
        rotulo = _secao_na_altura(blocos, top, secao_no_inicio.rotulo)
        blocos.append((top, Bloco("tabela", texto, rotulo)))

    return Pagina(
        pagina_pdf=indice,
        pagina_impressa=pagina_impressa(indice),
        blocos=tuple(anexar_legendas_de_tabela(blocos)),
    )


def _linha(bruta: dict) -> Linha:
    contagem = Counter((c["fontname"], round(c["size"], 1)) for c in bruta["chars"] if c["text"].strip())
    (fonte, tamanho), _ = contagem.most_common(1)[0] if contagem else (("", 0.0), 0)
    fonte_sem_prefixo = fonte.split("+")[-1]
    return Linha(
        texto=normalizar(bruta["text"]),
        tamanho=tamanho,
        negrito=fonte_sem_prefixo.endswith(("TB", "Bold", "-Bold")),
        x0=bruta["x0"],
        top=bruta["top"],
        fonte_tabela=fonte_sem_prefixo.startswith("Lato"),
    )


def _sem_rodape(linhas: list[Linha], esperado: int) -> list[Linha]:
    if linhas and linhas[-1].texto.strip() == str(esperado):
        return linhas[:-1]
    return linhas


def _secao_na_altura(blocos: list[tuple[float, Bloco]], top: float, padrao: str) -> str:
    acima = [b for t, b in blocos if t <= top]
    return acima[-1].secao if acima else padrao


def _tabelas_da_pagina(pagina_pdf) -> list[tuple[tuple[float, float, float, float], str]]:
    """Tabelas detectadas, já serializadas, com a caixa de cada uma.

    O pdfplumber parte uma tabela com filetes (booktabs) em vários pedaços: o
    cabeçalho, e cada grupo de linhas separado por filete ou espaço extra.
    Pedaços verticalmente colados (menos de 20 pt entre um e outro) e
    sobrepostos na horizontal são a mesma tabela, e são juntados.
    """
    brutas = []
    for tabela in pagina_pdf.find_tables():
        linhas = tabela.extract(x_tolerance=TOLERANCIA_X)
        linhas = [[normalizar(c) if c else c for c in l] for l in linhas]
        brutas.append([tabela.bbox, linhas])
    brutas.sort(key=lambda par: par[0][1])

    juntas: list[list] = []
    for bbox, linhas in brutas:
        if juntas:
            bbox_ant, linhas_ant = juntas[-1]
            colado = -2 <= bbox[1] - bbox_ant[3] < 20
            sobreposicao = min(bbox[2], bbox_ant[2]) - max(bbox[0], bbox_ant[0])
            largura = min(bbox[2] - bbox[0], bbox_ant[2] - bbox_ant[0])
            if colado and largura > 0 and sobreposicao / largura > 0.5:
                novo_bbox = (min(bbox_ant[0], bbox[0]), bbox_ant[1], max(bbox_ant[2], bbox[2]), bbox[3])
                juntas[-1] = [novo_bbox, linhas_ant + linhas]
                continue
        juntas.append([bbox, linhas])

    return [(tuple(bbox), serializar_tabela(linhas)) for bbox, linhas in juntas if linhas]

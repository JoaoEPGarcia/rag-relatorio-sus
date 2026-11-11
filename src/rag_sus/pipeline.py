# -*- coding: utf-8 -*-
"""O pipeline completo: da extração à conferência, na ordem, parando no primeiro erro.

POR QUE ISTO EXISTE. Quem clona o repositório precisa refazer tudo com um
comando, sem chamar o modelo e a partir das Rodadas versionadas. Este módulo
diz quais passos rodam, em que ordem, e quais são pulados (e por quê); a
casca scripts/reproduzir.py liga cada passo ao script de verdade. A Rodada
paga (scripts/03_rodar_avaliacao.py) nunca é um passo.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rag_sus import config
from rag_sus.avaliacao.sinteticas import rodada_sintetica

# O que a extração e o índice gravam (os caminhos de config, tomados sobre a raiz do pipeline).
# Se tudo existe, o passo é pulado: o índice exige o modelo de embeddings de 2,24 GB.
EXTRAIDOS = (config.TRECHOS, config.TEXTO_COMPLETO)
INDEXADOS = (config.INDICE / "indice.faiss", config.INDICE / "meta.json")


def _todos_existem(raiz: Path, caminhos: tuple[Path, ...]) -> bool:
    return all(config.na_raiz(c, raiz).exists() for c in caminhos)


@dataclass(frozen=True)
class Passo:
    nome: str
    executar: Callable[[], int]
    # Motivo para não rodar; None quando o passo roda.
    pulado: str | None = None


def passos_do_pipeline(
    raiz: Path, rodar_script: Callable[[str], int], compilar: Callable[[], int]
) -> list[Passo]:
    """Os passos sobre a raiz, na ordem. rodar_script recebe o nome do script em scripts/."""

    def script(nome: str) -> Callable[[], int]:
        return lambda: rodar_script(nome)

    extrair = not _todos_existem(raiz, EXTRAIDOS)
    indexar = extrair or not _todos_existem(raiz, INDEXADOS)
    so_pdf_real = None
    if rodada_sintetica(config.na_raiz(config.RODADAS, raiz) / "principal"):
        # Rodadas sintéticas: Gabarito sintético, e os números do corpus copiados do
        # registro do projeto. Nada aqui lê o PDF real, os Trechos ou o índice.
        extrair = indexar = False
        so_pdf_real = "Rodadas sintéticas: a raiz não tem o PDF real nem o Gabarito"
    return [
        Passo("extração", script("01_extrair.py"),
              None if extrair else so_pdf_real or "os Trechos já existem"),
        Passo("índice", script("02_indexar.py"), None if indexar else so_pdf_real or "o índice já existe"),
        Passo("análise", script("04_analisar.py")),
        Passo("figuras", script("05_figuras.py")),
        Passo("documentos", script("06_gerar_documentos.py")),
        Passo("compilação do Relatório de avaliação", compilar),
        Passo("conferidor de números", script("conferir_numeros.py")),
        Passo("conferência do Gabarito", script("conferir_gabarito.py"), so_pdf_real),
    ]


def _pdflatex(comando: list[str], cwd: Path) -> tuple[int, str]:
    r = subprocess.run(comando, cwd=cwd, capture_output=True)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", errors="replace")


# O que o pdflatex escreve no .log quando as referências pedem mais uma passada.
_PEDE_OUTRA_PASSADA = ("Rerun to get", "Label(s) may have changed")


def compilar_relatorio_de_avaliacao(
    tex: Path, pasta_saida: Path, executar: Callable[[list[str], Path], tuple[int, str]] = _pdflatex
) -> int:
    """Compila o Relatório de avaliação com o pdflatex rodando em pasta_saida.

    O .tex é o do projeto (escrito à mão, como o README.base.md); numeros.tex,
    tabelas/ e ../figuras/ ele acha a partir do diretório corrente, que é a
    pasta relatorio/ da raiz, e é lá que o PDF sai. Assim nada é copiado e, sobre
    uma raiz temporária, o PDF usa os números dela, e não os do projeto.
    """
    return compilar_pdf(tex, pasta_saida, "Relatório de avaliação", executar)


def compilar_pdf(
    tex: Path, pasta_saida: Path, nome: str,
    executar: Callable[[list[str], Path], tuple[int, str]] = _pdflatex,
) -> int:
    """Compila um .tex com o pdflatex rodando em pasta_saida: duas passadas, três se o .log pedir.

    Serve ao Relatório de avaliação e às folhas de Revisão; `nome` é o do
    documento nas mensagens. Devolve 0, ou o código do pdflatex que falhou.
    """
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    comando = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", str(tex)]
    log = pasta_saida / (Path(tex).stem + ".log")
    for passada in (1, 2, 3):
        try:
            codigo, saida = executar(comando, pasta_saida)
        except FileNotFoundError:
            print("pdflatex não encontrado: instale o MiKTeX (Windows) ou o TeX Live e ponha o pdflatex no PATH.")
            return 1
        if codigo != 0:
            print("\n".join(saida.splitlines()[-30:]))
            print(f"pdflatex falhou na passada {passada} (código {codigo}); o log completo está em {log}")
            return codigo
        pede_outra = log.exists() and any(t in log.read_text(encoding="utf-8", errors="replace")
                                           for t in _PEDE_OUTRA_PASSADA)
        if passada >= 2 and not pede_outra:
            break
    print(f"{nome}: {passada} passadas do pdflatex -> {pasta_saida / (Path(tex).stem + '.pdf')}")
    return 0


def rodar(passos: list[Passo]) -> int:
    """Roda os passos na ordem; no primeiro que falhar, diz qual foi e devolve o código dele (≠ 0)."""
    for passo in passos:
        if passo.pulado:
            print(f"== {passo.nome}: pulado ({passo.pulado})", flush=True)
            continue
        print(f"== {passo.nome}", flush=True)
        try:
            codigo = passo.executar()
        except Exception as erro:  # um passo que quebra também para o pipeline, com o nome dele
            print(f"{type(erro).__name__}: {erro}")
            codigo = 1
        if codigo != 0:
            print(f"Pipeline parado no passo «{passo.nome}» (código {codigo}).")
            return codigo
    print("Pipeline completo.")
    return 0

# -*- coding: utf-8 -*-
"""O pipeline completo (scripts/reproduzir.py): ordem dos passos, parada no primeiro erro, passos pulados.

Os testes rápidos usam passos falsos e raízes temporárias; nenhum dispara a
extração, o índice, o pdflatex nem o modelo.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from rag_sus import config
from rag_sus.avaliacao.sinteticas import gerar_rodadas_sinteticas
from rag_sus.pipeline import Passo, compilar_pdf, compilar_relatorio_de_avaliacao, passos_do_pipeline, rodar

ORDEM = [
    "extração",
    "índice",
    "análise",
    "figuras",
    "documentos",
    "compilação do Relatório de avaliação",
    "conferência do PDF",
    "conferidor de números",
    "conferência do Gabarito",
]


def raiz_com_corpus(tmp_path: Path) -> Path:
    """Uma raiz que já tem os Trechos, o texto completo e o índice (arquivos vazios bastam)."""
    for relativo in ("dados/trechos.jsonl", "dados/texto_completo.txt", "indice/indice.faiss", "indice/meta.json"):
        (tmp_path / relativo).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relativo).write_text("", encoding="utf-8")
    return tmp_path


class Registro:
    """Passos falsos que anotam o que rodou e devolvem o código pedido."""

    def __init__(self, codigos: dict[str, int] | None = None):
        self.rodados: list[str] = []
        self.codigos = codigos or {}

    def script(self, nome: str) -> int:
        self.rodados.append(nome)
        return self.codigos.get(nome, 0)

    def compilar(self) -> int:
        self.rodados.append("pdflatex")
        return self.codigos.get("pdflatex", 0)


def test_passos_na_ordem_do_ticket(tmp_path):
    passos = passos_do_pipeline(raiz_com_corpus(tmp_path), Registro().script, Registro().compilar)

    assert [p.nome for p in passos] == ORDEM


def pulados(passos) -> set[str]:
    return {p.nome for p in passos if p.pulado}


def test_extracao_e_indice_pulados_quando_os_arquivos_existem(tmp_path):
    passos = passos_do_pipeline(raiz_com_corpus(tmp_path), Registro().script, Registro().compilar)

    assert pulados(passos) == {"extração", "índice"}


def test_so_o_indice_roda_quando_falta_so_o_indice(tmp_path):
    raiz = raiz_com_corpus(tmp_path)
    (raiz / "indice" / "indice.faiss").unlink()

    assert pulados(passos_do_pipeline(raiz, Registro().script, Registro().compilar)) == {"extração"}


def test_sem_trechos_extrai_e_refaz_o_indice(tmp_path):
    raiz = raiz_com_corpus(tmp_path)
    (raiz / "dados" / "trechos.jsonl").unlink()

    assert pulados(passos_do_pipeline(raiz, Registro().script, Registro().compilar)) == set()


def test_raiz_sintetica_pula_o_que_depende_do_pdf_real(tmp_path):
    # As Rodadas sintéticas usam um Gabarito sintético e os números do corpus do
    # registro do projeto: a raiz não tem PDF, Trechos, índice nem Gabarito.
    gerar_rodadas_sinteticas(tmp_path, semente=2026, repeticoes=0)

    passos = passos_do_pipeline(tmp_path, Registro().script, Registro().compilar)

    assert pulados(passos) == {"extração", "índice", "conferência do Gabarito"}


def test_roda_todos_os_passos_na_ordem_menos_os_pulados(tmp_path, capsys):
    falsos = Registro()

    codigo = rodar(passos_do_pipeline(raiz_com_corpus(tmp_path), falsos.script, falsos.compilar))

    assert codigo == 0
    assert falsos.rodados == ["04_analisar.py", "05_figuras.py", "06_gerar_documentos.py", "pdflatex",
                              "conferir_pdf.py", "conferir_numeros.py", "conferir_gabarito.py"]
    saida = capsys.readouterr().out
    assert "extração: pulado (os Trechos já existem)" in saida
    assert saida.rstrip().endswith("Pipeline completo.")


def test_para_no_primeiro_erro_com_o_nome_do_passo_e_o_codigo(tmp_path, capsys):
    falsos = Registro({"05_figuras.py": 3})

    codigo = rodar(passos_do_pipeline(raiz_com_corpus(tmp_path), falsos.script, falsos.compilar))

    assert codigo == 3
    assert falsos.rodados == ["04_analisar.py", "05_figuras.py"]
    assert "Pipeline parado no passo «figuras» (código 3)" in capsys.readouterr().out


def test_passo_que_quebra_tambem_para_o_pipeline(tmp_path, capsys):
    def quebra() -> int:
        raise FileNotFoundError("pdflatex")

    codigo = rodar([Passo("compilação do Relatório de avaliação", quebra), Passo("conferidor de números", quebra)])

    assert codigo != 0
    saida = capsys.readouterr().out
    assert "Pipeline parado no passo «compilação do Relatório de avaliação»" in saida
    assert "pdflatex" in saida


class PdflatexFalso:
    """Anota cada chamada e grava o .log que o pdflatex gravaria na pasta de saída."""

    def __init__(self, logs: list[str], codigos: list[int] | None = None):
        self.chamadas: list[tuple[list[str], Path]] = []
        self.logs = logs
        self.codigos = codigos or [0] * len(logs)

    def __call__(self, comando: list[str], cwd: Path) -> tuple[int, str]:
        i = len(self.chamadas)
        self.chamadas.append((comando, cwd))
        (cwd / "relatorio.log").write_text(self.logs[i], encoding="utf-8")
        return self.codigos[i], f"saída da passada {i + 1}\n! Erro qualquer."


def test_compila_o_tex_do_projeto_com_entradas_e_saida_na_raiz(tmp_path):
    tex = tmp_path / "projeto" / "relatorio" / "relatorio.tex"
    pasta = tmp_path / "raiz" / "relatorio"
    pdflatex = PdflatexFalso(["Output written on relatorio.pdf", "Output written on relatorio.pdf"])

    assert compilar_relatorio_de_avaliacao(tex, pasta, pdflatex) == 0

    # O .tex fica no projeto; numeros.tex, tabelas/ e ../figuras/ se acham a partir do cwd, a raiz.
    comando = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", str(tex)]
    assert pdflatex.chamadas == [(comando, pasta), (comando, pasta)]


def test_terceira_passada_quando_o_log_pede(tmp_path):
    pdflatex = PdflatexFalso(["", "LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.",
                              ""])

    assert compilar_relatorio_de_avaliacao(tmp_path / "relatorio.tex", tmp_path, pdflatex) == 0
    assert len(pdflatex.chamadas) == 3


def test_passada_que_falha_para_a_compilacao_e_mostra_o_erro(tmp_path, capsys):
    pdflatex = PdflatexFalso(["", ""], codigos=[1, 0])

    assert compilar_relatorio_de_avaliacao(tmp_path / "relatorio.tex", tmp_path, pdflatex) == 1
    assert len(pdflatex.chamadas) == 1
    assert "! Erro qualquer." in capsys.readouterr().out


def test_folhas_de_revisao_compilam_pelo_mesmo_caminho_e_leem_o_log_pelo_nome_do_tex(tmp_path, capsys):
    # as folhas de Revisão (Gabarito, Veredictos) usam as mesmas passadas do Relatório de avaliação
    tex = tmp_path / "revisao_gabarito.tex"
    chamadas = []

    def pdflatex(comando, cwd):
        chamadas.append((comando, cwd))
        pede = "Rerun to get cross-references right." if len(chamadas) == 2 else ""
        (cwd / "revisao_gabarito.log").write_text(pede, encoding="utf-8")
        return 0, ""

    assert compilar_pdf(tex, tmp_path, "Folha de Revisão do Gabarito", pdflatex) == 0
    assert len(chamadas) == 3
    assert chamadas[0] == (["pdflatex", "-interaction=nonstopmode", "-halt-on-error", str(tex)], tmp_path)
    saida = capsys.readouterr().out
    assert "Folha de Revisão do Gabarito" in saida and str(tmp_path / "revisao_gabarito.pdf") in saida


def test_sem_pdflatex_diz_o_que_instalar(tmp_path, capsys):
    def ausente(comando, cwd):
        raise FileNotFoundError(comando[0])

    assert compilar_relatorio_de_avaliacao(tmp_path / "relatorio.tex", tmp_path, ausente) != 0
    assert "pdflatex não encontrado" in capsys.readouterr().out


# --- scripts/reproduzir.py de verdade, sobre raízes temporárias ---

SAIDAS = ("README.md", "NUMEROS_CANONICOS.md", "relatorio/numeros.tex", "relatorio/relatorio.pdf", "figuras")


def reproduzir(raiz: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "RAG_SUS_RAIZ": str(raiz)}
    return subprocess.run([sys.executable, str(config.PROJETO / "scripts" / "reproduzir.py")], env=env, cwd=raiz,
                          capture_output=True, text=True, encoding="utf-8")


def test_sem_rodada_principal_para_na_analise(tmp_path):
    r = reproduzir(raiz_com_corpus(tmp_path))

    assert r.returncode != 0
    assert "falta a Rodada principal" in r.stdout
    assert "Pipeline parado no passo «análise»" in r.stdout
    assert not any((tmp_path / s).exists() for s in SAIDAS)


def test_revisao_faltando_para_na_analise_sem_documento_parcial(tmp_path):
    gerar_rodadas_sinteticas(tmp_path, semente=2026, repeticoes=0)
    folha = tmp_path / "avaliacao" / "revisao_veredictos.csv"
    linhas = folha.read_text(encoding="utf-8").splitlines(keepends=True)
    folha.write_text("".join(linhas[:-1]), encoding="utf-8")  # apaga a Revisão da última linha
    registro = (tmp_path / "resultados" / "numeros.json").read_bytes()

    r = reproduzir(tmp_path)

    assert r.returncode != 0
    assert "sem Revisão" in r.stdout
    assert "Pipeline parado no passo «análise»" in r.stdout
    assert not any((tmp_path / s).exists() for s in SAIDAS)
    assert (tmp_path / "resultados" / "numeros.json").read_bytes() == registro


@pytest.mark.lento
@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="precisa do pdflatex")
def test_raiz_sintetica_de_ponta_a_ponta(tmp_path):
    def saidas_do_projeto():
        caminhos = ("README.md", "NUMEROS_CANONICOS.md", "relatorio/numeros.tex", "relatorio/relatorio.pdf",
                    "resultados/numeros.json")
        return {p: (config.PROJETO / p).read_bytes() if (config.PROJETO / p).exists() else None for p in caminhos}

    antes = saidas_do_projeto()
    gerar_rodadas_sinteticas(tmp_path, semente=2026, repeticoes=2)

    r = reproduzir(tmp_path)

    assert r.returncode == 0, r.stdout + r.stderr
    assert "Conferência dos números: ok" in r.stdout
    assert r.stdout.rstrip().endswith("Pipeline completo.")
    assert (tmp_path / "relatorio" / "relatorio.pdf").exists()
    assert saidas_do_projeto() == antes

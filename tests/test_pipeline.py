# -*- coding: utf-8 -*-
"""O pipeline completo (scripts/reproduzir.py): ordem dos passos, parada no primeiro erro, passos pulados.

Os testes rápidos usam passos falsos e raízes temporárias; nenhum dispara a
extração, o índice, o pdflatex nem o modelo.
"""

from pathlib import Path

from rag_sus.avaliacao.sinteticas import gerar_rodadas_sinteticas
from rag_sus.pipeline import Passo, passos_do_pipeline, rodar

ORDEM = [
    "extração",
    "índice",
    "análise",
    "figuras",
    "documentos",
    "compilação do Relatório de avaliação",
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
                              "conferir_numeros.py", "conferir_gabarito.py"]
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

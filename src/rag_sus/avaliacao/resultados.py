# -*- coding: utf-8 -*-
"""Da Rodada aos números: consolida a Rodada principal e registra os resultados.

POR QUE ISTO EXISTE. Os números publicados (README, Relatório de avaliação,
figuras) saem todos daqui, e nenhum é digitado (ADR 0003). `analisar` recebe
a pasta das Rodadas e a folha de Revisão dos Veredictos e:

- consolida a Rodada principal de cada Condição, exigindo a Revisão de todo
  Veredicto do Juiz; a Revisão do autor vence o Juiz;
- resume cada Condição (as três medidas com Wilson, respondíveis e sem
  resposta em separado, tokens, latência e fallbacks);
- compara com RAG × sem RAG (comparação principal) e com RAG × contexto
  completo, pareando pelo id;
- cruza as Classes de erro com o Tipo de pergunta na Condição com RAG;
- mede a concordância com cada repetição que existir (Veredictos não
  revisados);
- grava cada número no registro, numa vez só, e escreve as linhas das tabelas
  do Relatório de avaliação, que o kit lê com \\linhasde.
"""

from __future__ import annotations

from pathlib import Path

from rag_sus import config, numeros
from rag_sus.assistente import CONDICOES
from rag_sus.avaliacao.analise import comparar, resumir
from rag_sus.avaliacao.rodada import RevisaoIncompleta, consolidar
from rag_sus.numeros import Numero

SCRIPT = "scripts/04_analisar.py"
NOMES_CONDICAO = {"com_rag": "com RAG", "sem_rag": "sem RAG", "contexto_completo": "contexto completo"}
# Com RAG contra cada uma das outras; a primeira é a comparação principal.
COMPARADAS_COM_RAG = ("sem_rag", "contexto_completo")


def _intervalo(chave: str, intervalo, o_que: str) -> list[Numero]:
    return [
        Numero(chave, intervalo.proporcao, o_que, "pct1"),
        Numero(f"{chave}_inf", intervalo.inferior, f"{o_que}: limite inferior do IC de Wilson de 95%", "pct1"),
        Numero(f"{chave}_sup", intervalo.superior, f"{o_que}: limite superior do IC de Wilson de 95%", "pct1"),
    ]


def _numeros_da_condicao(c: str, r: dict) -> list[Numero]:
    nome = NOMES_CONDICAO[c]
    lista = [
        Numero(f"{c}_n_respondiveis", r["n_respondiveis"], f"Perguntas respondíveis na Condição {nome}"),
        Numero(f"{c}_acertos_resposta", r["acertos_resposta"], f"acertos da resposta {nome} (respondíveis)"),
    ]
    lista += _intervalo(f"{c}_acerto_resposta", r["acerto_resposta"], f"Acerto da resposta {nome} (respondíveis)")
    if r["abstencao_correta"]:
        lista += [
            Numero(f"{c}_n_sem_resposta", r["n_sem_resposta"], f"Perguntas sem resposta na Condição {nome}"),
            Numero(f"{c}_abstencoes_corretas", r["abstencoes_corretas"], f"Abstenções corretas {nome} (sem resposta)"),
        ]
        lista += _intervalo(f"{c}_abstencao_correta", r["abstencao_correta"],
                            f"Abstenção correta {nome} (sem resposta)")
    return lista


def _numeros_de_destaque(resumos: dict[str, dict]) -> list[Numero]:
    """Acerto da resposta com RAG nas respondíveis, com IC, contra o mesmo acerto sem RAG."""
    com, sem = resumos["com_rag"], resumos["sem_rag"]
    lista = [Numero("destaque_n_respondiveis", com["n_respondiveis"],
                    "destaque: Perguntas respondíveis em que o acerto é medido")]
    lista += _intervalo("destaque_acerto_com_rag", com["acerto_resposta"],
                        "destaque: Acerto da resposta com RAG (respondíveis)")
    lista.append(Numero("destaque_acerto_sem_rag", sem["acerto_resposta"].proporcao,
                        "destaque: Acerto da resposta sem RAG (respondíveis)", "pct1"))
    return lista


def _consolidar_principal(principal: Path, folha: Path) -> dict[str, list[dict]]:
    """Consolida as três Condições e, se faltar Revisão, lista as pendentes de todas de uma vez."""
    consolidadas, pendentes = {}, []
    for c in CONDICOES:
        linhas = consolidar(principal / f"{c}.jsonl", folha, exigir_revisao=False)
        consolidadas[c] = linhas
        faltando = [l["id"] for l in linhas if l["veredicto_juiz"] is not None and not l["revisado_pelo_autor"]]
        if faltando:
            pendentes.append(f"{c}: {', '.join(faltando)}")
    if pendentes:
        raise RevisaoIncompleta(
            f"há Veredicto do Juiz sem Revisão na Rodada principal ({'; '.join(pendentes)}). "
            f"Preencha veredicto_revisado (certo/errado) em {Path(folha).name} e rode de novo."
        )
    return consolidadas


def _numeros_da_comparacao(outra: str, com_rag: list[dict], linhas_outra: list[dict]) -> list[Numero]:
    k = f"com_rag_x_{outra}"
    nome = f"com RAG × {NOMES_CONDICAO[outra]}"
    c = comparar(com_rag, linhas_outra)
    t, d = c["tabela"], c["diferenca"]
    return [
        Numero(f"{k}_n_pares", t.n, f"{nome}: Perguntas respondíveis pareadas"),
        Numero(f"{k}_ambos", t.ambos, f"{nome}: as duas Condições acertam"),
        Numero(f"{k}_so_com_rag", t.so_a, f"{nome}: só com RAG acerta"),
        Numero(f"{k}_so_{outra}", t.so_b, f"{nome}: só {NOMES_CONDICAO[outra]} acerta"),
        Numero(f"{k}_nenhum", t.nenhum, f"{nome}: as duas Condições erram"),
        Numero(f"{k}_diferenca", d.diferenca, f"{nome}: diferença pareada do Acerto da resposta", "pp1"),
        Numero(f"{k}_diferenca_inf", d.inferior, f"{nome}: limite inferior do IC de Newcombe de 95%", "pp1"),
        Numero(f"{k}_diferenca_sup", d.superior, f"{nome}: limite superior do IC de Newcombe de 95%", "pp1"),
        Numero(f"{k}_p_mcnemar", c["p_mcnemar"], f"{nome}: valor-p do teste exato de McNemar", "p3"),
    ]


def _numeros_da_revisao(consolidadas: dict[str, list[dict]]) -> list[Numero]:
    do_juiz = [l for linhas in consolidadas.values() for l in linhas if l["veredicto_juiz"] is not None]
    revisados = [l for l in do_juiz if l["revisado_pelo_autor"]]
    mudados = [l for l in revisados if l["acerto_resposta"] != l["veredicto_juiz"]]
    return [
        Numero("revisao_veredictos_juiz", len(do_juiz), "Veredictos do Juiz na Rodada principal (três Condições)"),
        Numero("revisao_veredictos_revisados", len(revisados), "Veredictos do Juiz revisados pelo autor"),
        Numero("revisao_veredictos_mudados", len(mudados), "Veredictos do Juiz que a Revisão do autor mudou"),
    ]


def analisar(
    pasta_rodadas: Path,
    folha: Path,
    numeros_json: Path | None = None,
    pasta_tabelas: Path | None = None,
) -> dict[str, str]:
    """Registra os números da Rodada principal e devolve chave -> texto formatado."""
    consolidadas = _consolidar_principal(Path(pasta_rodadas) / "principal", folha)
    resumos = {c: resumir(consolidadas[c]) for c in CONDICOES}
    lista: list[Numero] = _numeros_de_destaque(resumos) + _numeros_da_revisao(consolidadas)
    for c in CONDICOES:
        lista += _numeros_da_condicao(c, resumos[c])
    for outra in COMPARADAS_COM_RAG:
        lista += _numeros_da_comparacao(outra, consolidadas["com_rag"], consolidadas[outra])
    return numeros.registrar_do_script(SCRIPT, lista, caminho=numeros_json or config.NUMEROS)

# -*- coding: utf-8 -*-
"""Rodadas sintéticas de demonstração, para verificar o pipeline sem chamar o modelo.

POR QUE ISTO EXISTE. As figuras, o Relatório de avaliação e o pipeline
completo precisam ser conferidos antes da Rodada principal, que depende da
chave da API e da Revisão do autor. Este módulo grava, numa raiz temporária,
Rodadas com a mesma forma das reais: 50 Perguntas respondíveis (10 de cada
Tipo de pergunta) e 10 sem resposta, nas três Condições, com a folha de
Revisão já preenchida e as repetições. O registro da raiz recebe também os
números do corpus (páginas, palavras, Trechos), copiados do registro do
projeto: eles saem do PDF real e o README os pede.

Os números são inventados, e por isso nunca podem chegar ao registro real:

- `gerar_rodadas_sinteticas` recusa gravar numa cópia do projeto (uma pasta
  com pyproject.toml, ou dentro dela);
- cada Rodada grava execucao.json com "sintetica": true, e a análise recusa
  publicar Rodadas sintéticas no registro de uma cópia do projeto.

As linhas saem do próprio `executar_rodada`, com um assistente e um Juiz
falsos, para que o formato nunca se afaste do das Rodadas reais. A mesma
semente gera sempre os mesmos arquivos.
"""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path

from rag_sus import config, numeros
from rag_sus.assistente import CONDICOES, RespostaAssistente
from rag_sus.avaliacao.gabarito import TIPOS_RESPONDIVEIS, ItemGabarito
from rag_sus.avaliacao.juiz import Veredicto
from rag_sus.avaliacao.rodada import COLUNAS_FOLHA, executar_rodada, gravar_folha_de_revisao
from rag_sus.avaliacao.travas import RODADAS_PUBLICADAS
from rag_sus.numeros import Numero, formatar
from rag_sus.provedores import Metadados

MODELO = "gemini-3.8-flash"
# Os números do corpus (páginas, palavras, Trechos) saem do PDF real por este script.
SCRIPT_DO_CORPUS = "scripts/01_extrair.py"
# O registro do projeto, e não o de RAG_SUS_RAIZ: dele só se leem os números do corpus.
NUMEROS_DO_PROJETO = config.PROJETO / "resultados" / "numeros.json"

# Probabilidade de acertar a resposta, por Condição e Tipo de pergunta; nas sem
# resposta, de se abster. Escolhidas para o resultado parecer plausível.
_ACERTO = {
    "com_rag": {"numero_prosa": 0.9, "numero_tabela": 0.75, "numero_legenda": 0.85, "conceito": 0.8,
                "sintese": 0.6, "sem_resposta": 0.9},
    "sem_rag": {"numero_prosa": 0.15, "numero_tabela": 0.1, "numero_legenda": 0.1, "conceito": 0.5,
                "sintese": 0.3, "sem_resposta": 0.6},
    "contexto_completo": {"numero_prosa": 0.9, "numero_tabela": 0.8, "numero_legenda": 0.85, "conceito": 0.85,
                          "sintese": 0.7, "sem_resposta": 0.9},
}
_CUSTO = {  # tokens de entrada, tokens lidos do cache e latência (s), mínimo e máximo
    "com_rag": ((2200, 3200), (0, 0), (1.5, 4.0)),
    "sem_rag": ((150, 300), (0, 0), (0.8, 2.5)),
    "contexto_completo": ((90000, 98000), (80000, 88000), (6.0, 15.0)),
}
_MUDA_NA_REPETICAO = 0.08  # fração dos Veredictos que mudam de uma Rodada para outra
_JUIZ_ERRA = 0.12  # fração dos Veredictos do Juiz que a Revisão do autor corrige


class RaizProibida(ValueError):
    pass


def dentro_de_uma_copia_do_projeto(caminho: Path) -> bool:
    caminho = Path(caminho).resolve()
    return any((p / "pyproject.toml").exists() for p in (caminho, *caminho.parents))


def rodada_sintetica(pasta_rodada: Path) -> bool:
    execucao = Path(pasta_rodada) / "execucao.json"
    return execucao.exists() and json.loads(execucao.read_text(encoding="utf-8")).get("sintetica", False)


@dataclass(frozen=True)
class _Plano:
    acerto: bool
    abstencao: bool
    citacao: bool
    recuperacao: bool
    juiz_erra: bool


def gabarito_sintetico() -> list[ItemGabarito]:
    itens = []
    for n in range(50):
        tipo = TIPOS_RESPONDIVEIS[n // 10]
        valor = float(1000 + 37 * n)
        numerico = tipo.startswith("numero_")
        itens.append(ItemGabarito(
            id=f"G{n + 1:02d}",
            pergunta=f"Pergunta sintética G{n + 1:02d}, do Tipo {tipo}?",
            tipo=tipo,
            resposta=f"Foram {formatar(valor, 'inteiro')} internações." if numerico else "Resposta descritiva.",
            valores=(valor,) if numerico else (),
            paginas=(10 + n,) if tipo != "sintese" else (10 + n, 120 + n),
            revisado="sintético",
        ))
    for n in range(10):
        itens.append(ItemGabarito(f"S{n + 1:02d}", f"Pergunta sintética S{n + 1:02d}, sem resposta?",
                                  "sem_resposta", "", (), (), "sintético"))
    return itens


def _planos(itens: list[ItemGabarito], condicao: str, rng: random.Random) -> dict[str, _Plano]:
    planos = {}
    for item in itens:
        acerto = rng.random() < _ACERTO[condicao][item.tipo]
        if not item.respondivel:
            planos[item.id] = _Plano(acerto, abstencao=acerto, citacao=False, recuperacao=False, juiz_erra=False)
            continue
        abstencao = not acerto and rng.random() < 0.3
        recuperacao = rng.random() < (0.97 if acerto else 0.5)
        planos[item.id] = _Plano(acerto, abstencao, citacao=acerto and rng.random() < 0.92,
                                 recuperacao=recuperacao, juiz_erra=rng.random() < _JUIZ_ERRA)
    return planos


def _variar(planos: dict[str, _Plano], rng: random.Random) -> dict[str, _Plano]:
    """Uma repetição: a maioria dos Veredictos se repete, alguns mudam."""
    saida = {}
    for id_, p in sorted(planos.items()):
        if rng.random() < _MUDA_NA_REPETICAO:
            acerto = not p.acerto
            sem_resposta = id_.startswith("S")
            p = _Plano(acerto, abstencao=acerto if sem_resposta else False, citacao=acerto and not sem_resposta,
                       recuperacao=p.recuperacao, juiz_erra=p.juiz_erra)
        saida[id_] = p
    return saida


class _AssistenteSintetico:
    def __init__(self, itens: list[ItemGabarito], planos: dict[str, _Plano], condicao: str, rng: random.Random):
        self.por_pergunta = {i.pergunta: i for i in itens}
        self.planos, self.condicao, self.rng = planos, condicao, rng

    def responder(self, pergunta: str, condicao: str) -> RespostaAssistente:
        item = self.por_pergunta[pergunta]
        p = self.planos[item.id]
        pagina = item.paginas[0] if item.paginas else 1
        if p.abstencao:
            texto, citadas = "O relatório não trata deste assunto.", ()
        elif item.numerico:
            valor = item.valores[0] if p.acerto else item.valores[0] + 11
            texto, citadas = f"Foram {formatar(valor, 'inteiro')} internações.", (pagina if p.citacao else pagina + 1,)
        else:
            texto, citadas = "Resposta descritiva sintética.", (pagina if p.citacao else pagina + 1,)
        recuperadas = (pagina, pagina + 2) if p.recuperacao else (pagina + 60, pagina + 61)
        (tmin, tmax), (cmin, cmax), (lmin, lmax) = _CUSTO[self.condicao]
        meta = Metadados(
            modelo_pedido=MODELO,
            modelo_que_respondeu=MODELO,
            usou_fallback=False,
            tokens_entrada=self.rng.randint(tmin, tmax),
            tokens_saida=self.rng.randint(40, 220),
            tokens_cache_leitura=self.rng.randint(cmin, cmax) if cmax else 0,
            latencia_s=round(self.rng.uniform(lmin, lmax), 2),
            id_requisicao=f"sintetica-{self.condicao}-{item.id}",
        )
        return RespostaAssistente(condicao, texto, citadas, p.abstencao,
                                  recuperadas if condicao == "com_rag" else (), (), meta)


class _JuizSintetico:
    def __init__(self, itens: list[ItemGabarito], planos: dict[str, _Plano]):
        self.por_pergunta = {i.pergunta: i for i in itens}
        self.planos = planos

    def julgar(self, pergunta: str, gabarito: str, resposta: str) -> Veredicto:
        p = self.planos[self.por_pergunta[pergunta].id]
        return Veredicto(p.acerto != p.juiz_erra, "Justificativa sintética.", Metadados(MODELO, MODELO, False))


def _revisar_folha(folha: Path, planos: dict[str, dict[str, _Plano]]) -> None:
    """Preenche a folha como o autor faria: o Veredicto verdadeiro, que às vezes contraria o Juiz."""
    with open(folha, encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    for l in linhas:
        p = planos[l["condicao"]][l["id"]]
        l["veredicto_revisado"] = "certo" if p.acerto else "errado"
        l["comentario"] = "Revisão sintética." if p.juiz_erra else ""
    with open(folha, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS_FOLHA, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def _copiar_numeros_do_corpus(numeros_do_projeto: Path, destino: Path) -> None:
    """Registra na raiz temporária os números do corpus que o registro do projeto já tem.

    Eles saem do PDF real (scripts/01_extrair.py), e não das Rodadas: são
    reais, e o README os pede na tabela do topo. Cada um é registrado de novo
    a partir do valor e do formato, para sair com o texto nos dois idiomas
    mesmo que o registro do projeto seja de uma versão anterior.
    """
    do_corpus = [
        Numero(chave, e["valor"], e["descricao"], e["formato"], tuple(e.get("aparece_em", ())))
        for chave, e in numeros.carregar(numeros_do_projeto).items()
        if e.get("script") == SCRIPT_DO_CORPUS
    ]
    if do_corpus:
        numeros.registrar_do_script(SCRIPT_DO_CORPUS, do_corpus, caminho=destino)


def gerar_rodadas_sinteticas(
    raiz: Path, semente: int = 2026, repeticoes: int = 2, numeros_do_projeto: Path | None = None
) -> Path:
    """Grava a Rodada principal, a folha revisada e `repeticoes` repetições em `raiz`.

    Devolve a pasta das Rodadas (`raiz/resultados/rodadas`). A folha fica em
    `raiz/avaliacao/revisao_veredictos.csv`, como no projeto. O registro
    `raiz/resultados/numeros.json` recebe os números reais do corpus, lidos de
    `numeros_do_projeto` (padrão: o registro do projeto, que nunca é escrito).
    """
    raiz = Path(raiz)
    if dentro_de_uma_copia_do_projeto(raiz):
        raise RaizProibida(
            f"{raiz} é (ou está dentro de) uma cópia do projeto: as Rodadas sintéticas só vão para uma raiz "
            "temporária, nunca para resultados/ de verdade"
        )
    if not 0 <= repeticoes <= len(RODADAS_PUBLICADAS) - 1:
        raise ValueError(f"repeticoes vai de 0 a {len(RODADAS_PUBLICADAS) - 1}")

    pasta_rodadas = raiz / "resultados" / "rodadas"
    folha = raiz / "avaliacao" / "revisao_veredictos.csv"
    for antigo in [*pasta_rodadas.glob("*/*.jsonl"), *pasta_rodadas.glob("*/execucao.json"), folha]:
        antigo.unlink(missing_ok=True)

    itens = gabarito_sintetico()
    planos = {c: _planos(itens, c, random.Random(f"{semente}-{c}")) for c in CONDICOES}
    for numero, rodada in enumerate(RODADAS_PUBLICADAS[: repeticoes + 1]):
        pasta = pasta_rodadas / rodada
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "execucao.json").write_text(
            json.dumps({"sintetica": True, "semente": semente, "commit": "sintetico"}, ensure_ascii=False, indent=2)
            + "\n", encoding="utf-8", newline="\n")
        for c in CONDICOES:
            plano = planos[c] if numero == 0 else _variar(planos[c], random.Random(f"{semente}-{rodada}-{c}"))
            assistente = _AssistenteSintetico(itens, plano, c, random.Random(f"{semente}-{rodada}-{c}-custo"))
            executar_rodada(itens, c, assistente, _JuizSintetico(itens, plano), pasta / f"{c}.jsonl")

    gravar_folha_de_revisao([pasta_rodadas / "principal" / f"{c}.jsonl" for c in CONDICOES], folha)
    _revisar_folha(folha, planos)
    _copiar_numeros_do_corpus(Path(numeros_do_projeto or NUMEROS_DO_PROJETO), raiz / "resultados" / "numeros.json")
    return pasta_rodadas

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
- escolhe, a partir do resultado, os textos que o README imprime ao lado dos
  números (a conclusão de cada comparação pelo IC da diferença e a Classe de
  erro mais frequente com RAG), em português e em inglês, para que nenhuma
  frase do README fixe um achado que o resultado não sustente;
- registra os parâmetros com que a Rodada principal rodou (k, modelos,
  commit), lidos do execucao.json dela, para o Relatório de avaliação
  citá-los sem digitar;
- grava cada número no registro, numa vez só, e escreve as linhas das tabelas
  do Relatório de avaliação, que o kit lê com \\linhasde.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

from rag_sus import config, numeros
from rag_sus.assistente import CONDICOES
from rag_sus.avaliacao import estatistica
from rag_sus.avaliacao.analise import comparar, concordancia, erros_por_tipo, resumir
from rag_sus.avaliacao.gabarito import TIPOS_RESPONDIVEIS
from rag_sus.avaliacao.rodada import RevisaoIncompleta, carregar_linhas, consolidar
from rag_sus.avaliacao.sinteticas import recusar_no_projeto, rodada_sintetica
from rag_sus.avaliacao.travas import RODADAS_PUBLICADAS
from rag_sus.avaliacao.vocabulario import (
    CLASSES_DAS_RESPONDIVEIS,
    CLASSES_DE_ERRO,
    CONCLUSOES,
    NOMES_CONDICAO,
    NOMES_TIPO,
    SO_NAS_SEM_RESPOSTA,
    chave_por_tipo,
    juntar,
    lado_do_ic,
    mais_frequentes,
    rotulo_condicao,
)
from rag_sus.documentos import texto_tex
from rag_sus.numeros import Numero, Texto

REPETICOES = tuple(r for r in RODADAS_PUBLICADAS if r != "principal")
# O nome de cada repetição na tabela de concordância, por extenso (sem dígito digitado no Relatório).
NOMES_REPETICAO = {"repeticao1": "Primeira repetição", "repeticao2": "Segunda repetição"}

SCRIPT = "scripts/04_analisar.py"
TABELAS_NO_PROJETO = "relatorio/tabelas"  # como a coluna "Onde aparece" cita os arquivos de linhas
# Com RAG contra cada uma das outras; a primeira é a comparação principal.
COMPARADAS_COM_RAG = ("sem_rag", "contexto_completo")


def _nivel() -> int:
    """O nível dos intervalos em %, lido da estatística na hora, para nenhuma descrição o digitar."""
    return round(100 * estatistica.NIVEL)


def _intervalo(chave: str, intervalo, o_que: str) -> list[Numero]:
    ic = f"IC de Wilson de {_nivel()}%"
    return [
        Numero(chave, intervalo.proporcao, o_que, "pct1"),
        Numero(f"{chave}_inf", intervalo.inferior, f"{o_que}: limite inferior do {ic}", "pct1"),
        Numero(f"{chave}_sup", intervalo.superior, f"{o_que}: limite superior do {ic}", "pct1"),
    ]


def _numeros_da_condicao(c: str, r: dict) -> list[Numero]:
    nome = NOMES_CONDICAO[c]
    lista = [
        Numero(f"{c}_n_respondiveis", r["n_respondiveis"], f"Perguntas respondíveis na Condição {nome}"),
        Numero(f"{c}_acertos_resposta", r["acertos_resposta"], f"acertos da resposta {nome} (respondíveis)"),
    ]
    lista += _intervalo(f"{c}_acerto_resposta", r["acerto_resposta"], f"Acerto da resposta {nome} (respondíveis)")
    lista.append(Numero(f"{c}_acertos_citacao", r["acertos_citacao"], f"acertos da citação {nome} (respondíveis)"))
    lista += _intervalo(f"{c}_acerto_citacao", r["acerto_citacao"], f"Acerto da citação {nome} (respondíveis)")
    if r["acerto_recuperacao"]:
        lista.append(Numero(f"{c}_acertos_recuperacao", r["acertos_recuperacao"],
                            f"acertos da recuperação {nome} (respondíveis)"))
        lista += _intervalo(f"{c}_acerto_recuperacao", r["acerto_recuperacao"],
                            f"Acerto da recuperação {nome} (respondíveis)")
    lista += [
        Numero(f"{c}_tokens_entrada_total", r["tokens_entrada_total"], f"tokens de entrada {nome}, soma da Rodada"),
        Numero(f"{c}_tokens_entrada_medio", r["tokens_entrada_medio"], f"tokens de entrada {nome}, média por Pergunta",
               "inteiro"),
        Numero(f"{c}_tokens_saida_total", r["tokens_saida_total"], f"tokens de saída {nome}, soma da Rodada"),
        Numero(f"{c}_tokens_cache_leitura_total", r["tokens_cache_leitura_total"],
               f"tokens de entrada lidos do cache {nome}, soma da Rodada"),
        Numero(f"{c}_latencia_mediana_s", r["latencia_mediana_s"], f"latência mediana por Pergunta {nome}, em segundos",
               "dec1"),
        Numero(f"{c}_n_fallback", r["n_fallback"], f"respostas {nome} dadas por outro modelo (fallback do servidor)"),
    ]
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
    ausentes = [c for c in CONDICOES if not (principal / f"{c}.jsonl").exists()]
    if ausentes:
        raise FileNotFoundError(
            f"falta a Rodada principal de {', '.join(ausentes)} em {principal}: "
            "rode scripts/03_rodar_avaliacao.py --rodada principal"
        )
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


def _numeros_dos_erros(c: str, r: dict) -> list[Numero]:
    nome = NOMES_CONDICAO[c]
    return [
        Numero(f"{c}_erros_{slug}", r["erros"].get(classe.nome, 0),
               f"Classe de erro '{classe.nome}' {nome} (Perguntas)")
        for slug, classe in CLASSES_DE_ERRO.items()
    ]


def _numeros_por_tipo(linhas: list[dict]) -> list[Numero]:
    """Classes de erro cruzadas com o Tipo de pergunta, na Condição com RAG."""
    cruzamento = erros_por_tipo(linhas)
    lista: list[Numero] = []
    for tipo in TIPOS_RESPONDIVEIS:
        celula = cruzamento.get(tipo, {})
        nome = NOMES_TIPO[tipo]
        acertos = sum(l["acerto_resposta"] for l in linhas if l["tipo"] == tipo)
        lista += [
            Numero(chave_por_tipo(tipo, "n"), celula.get("n", 0), f"Perguntas do Tipo '{nome}'"),
            Numero(chave_por_tipo(tipo, "acertos"), acertos, f"acertos da resposta com RAG, Tipo '{nome}'"),
        ]
        lista += [
            Numero(chave_por_tipo(tipo, slug), celula.get(CLASSES_DE_ERRO[slug].nome, 0),
                   f"'{CLASSES_DE_ERRO[slug].nome}' com RAG, Tipo '{nome}'")
            for slug in CLASSES_DAS_RESPONDIVEIS
        ]
    sem = [l for l in linhas if not l["respondivel"]]
    inventada = CLASSES_DE_ERRO[SO_NAS_SEM_RESPOSTA].nome
    lista += [
        Numero(chave_por_tipo("sem_resposta", "n"), len(sem), "Perguntas sem resposta"),
        Numero(chave_por_tipo("sem_resposta", "acertos"), sum(l["acerto_resposta"] for l in sem),
               "abstenções corretas com RAG nas Perguntas sem resposta"),
        Numero(chave_por_tipo("sem_resposta", SO_NAS_SEM_RESPOSTA), sum(l["classe_erro"] == inventada for l in sem),
               f"'{inventada}' com RAG nas Perguntas sem resposta"),
    ]
    return lista


def _numeros_do_erro_mais_frequente(c: str, r: dict) -> list[Numero | Texto]:
    """A Classe de erro mais frequente na Condição, escolhida aqui para o README não fixá-la à mão.

    Empate: todas as empatadas, na ordem de CLASSES_DE_ERRO. Sem erro nenhum,
    o texto diz isso, para a frase do README continuar verdadeira.
    """
    nome = NOMES_CONDICAO[c]
    contagem = {slug: r["erros"].get(classe.nome, 0) for slug, classe in CLASSES_DE_ERRO.items()}
    mais = mais_frequentes(contagem)
    maior = contagem[mais[0]] if mais else 0
    if not mais:
        pt, en = "nenhuma, porque não houve erro", "none, since there was no error"
    else:
        pt = juntar([CLASSES_DE_ERRO[s].nome for s in mais], "e")
        en = juntar([CLASSES_DE_ERRO[s].nome_en for s in mais], "and")
        if len(mais) > 1:
            pt, en = f"{pt}, empatadas", f"{en}, tied"
    return [
        Numero(f"{c}_n_com_erro", sum(contagem.values()),
               f"respostas {nome} com alguma Classe de erro (respondíveis e sem resposta)"),
        Numero(f"{c}_erro_mais_frequente_n", maior, f"respostas {nome} na Classe de erro mais frequente"),
        Texto(f"{c}_erro_mais_frequente", pt, en, f"Classe de erro mais frequente {nome} (empates juntos)"),
    ]


def _conclusao(outra: str, d) -> Texto:
    """O que o IC da diferença pareada permite dizer: com RAG acerta mais, menos, ou os dados não distinguem."""
    pt, en = CONCLUSOES[lado_do_ic(d.inferior, d.superior)]
    return Texto(f"com_rag_x_{outra}_conclusao", pt, en,
                 f"com RAG × {NOMES_CONDICAO[outra]}: leitura do IC de Newcombe (todo acima, todo abaixo "
                 "de zero ou incluindo o zero)")


def _numeros_da_comparacao(outra: str, com_rag: list[dict], linhas_outra: list[dict]) -> list[Numero | Texto]:
    k = f"com_rag_x_{outra}"
    nome = f"com RAG × {NOMES_CONDICAO[outra]}"
    c = comparar(com_rag, linhas_outra)
    t, d = c["tabela"], c["diferenca"]
    ic = f"IC de Newcombe de {_nivel()}%"
    return [
        _conclusao(outra, d),
        Numero(f"{k}_n_pares", t.n, f"{nome}: Perguntas respondíveis pareadas"),
        Numero(f"{k}_ambos", t.ambos, f"{nome}: as duas Condições acertam"),
        Numero(f"{k}_so_com_rag", t.so_a, f"{nome}: só com RAG acerta"),
        Numero(f"{k}_so_{outra}", t.so_b, f"{nome}: só {NOMES_CONDICAO[outra]} acerta"),
        Numero(f"{k}_nenhum", t.nenhum, f"{nome}: as duas Condições erram"),
        Numero(f"{k}_diferenca", d.diferenca, f"{nome}: diferença pareada do Acerto da resposta", "pp1"),
        Numero(f"{k}_diferenca_inf", d.inferior, f"{nome}: limite inferior do {ic}", "pp1"),
        Numero(f"{k}_diferenca_sup", d.superior, f"{nome}: limite superior do {ic}", "pp1"),
        Numero(f"{k}_p_mcnemar", c["p_mcnemar"], f"{nome}: valor-p do teste exato de McNemar", "p3"),
    ]


def _numeros_do_gabarito(linhas: list[dict]) -> list[Numero]:
    """O tamanho do Gabarito avaliado, contado nas linhas da Rodada principal com RAG."""
    respondiveis = [l for l in linhas if l["respondivel"]]
    return [
        Numero("gabarito_n_perguntas", len(linhas), "Perguntas do Gabarito avaliadas"),
        Numero("gabarito_n_respondiveis", len(respondiveis), "Perguntas respondíveis do Gabarito"),
        Numero("gabarito_n_sem_resposta", len(linhas) - len(respondiveis), "Perguntas sem resposta do Gabarito"),
        Numero("gabarito_n_tipos", len({l["tipo"] for l in respondiveis}), "Tipos de pergunta entre as respondíveis"),
    ]


def _numeros_da_rodada(resumos: dict[str, dict]) -> list[Numero]:
    """Totais da Rodada principal nas três Condições."""
    def soma(campo: str) -> int:
        return sum(r[campo] for r in resumos.values())

    return [
        Numero("principal_n_respostas", soma("n_respondiveis") + soma("n_sem_resposta"),
               "respostas na Rodada principal (Perguntas × Condições)"),
        Numero("principal_tokens_entrada_total", soma("tokens_entrada_total"),
               "tokens de entrada na Rodada principal, três Condições"),
        Numero("principal_tokens_saida_total", soma("tokens_saida_total"),
               "tokens de saída na Rodada principal, três Condições"),
        Numero("principal_n_fallback", soma("n_fallback"),
               "respostas da Rodada principal dadas por outro modelo (fallback do servidor)"),
    ]


def _numeros_da_concordancia(pasta_rodadas: Path) -> list[Numero | Texto]:
    """Concordância entre a Rodada principal e cada repetição que existir, por Condição.

    Compara os Veredictos automáticos (Juiz ou regra), sem a Revisão: as
    repetições não são revisadas, e a principal entra do mesmo jeito para a
    comparação ser justa.
    """
    lista: list[Numero | Texto] = []
    existentes = [r for r in REPETICOES if any(carregar_linhas(pasta_rodadas / r / f"{c}.jsonl") for c in CONDICOES)]
    lista.append(Numero("repeticoes_comparadas", len(existentes),
                        "repetições da Rodada principal comparadas com ela (Veredictos não revisados)"))
    if existentes:
        pt = "Para medir isso, a Rodada principal foi repetida, e cada repetição é comparada com ela."
        en = "To measure this, the main run was repeated and compared with each repeat."
    else:
        pt = ("A Rodada principal não foi repetida: sem repetição, não há concordância a medir, e a tabela "
              "abaixo sai vazia.")
        en = "The main run was not repeated: without a repeat there is no agreement to measure."
    lista.append(Texto("repeticoes_leitura", pt, en,
                       "frase do Relatório de avaliação sobre as repetições, escolhida por repeticoes_comparadas"))
    for rodada in REPETICOES:
        for c in CONDICOES:
            repeticao = carregar_linhas(pasta_rodadas / rodada / f"{c}.jsonl")
            principal = carregar_linhas(pasta_rodadas / "principal" / f"{c}.jsonl")
            if not repeticao:
                continue
            comuns = {l["id"] for l in principal} & {l["id"] for l in repeticao}
            o_que = f"concordância entre a Rodada principal e a {rodada}, {NOMES_CONDICAO[c]}"
            lista += [
                Numero(f"concordancia_{rodada}_{c}", concordancia(principal, repeticao),
                       f"{o_que} (Veredictos não revisados)", "pct1"),
                Numero(f"concordancia_{rodada}_{c}_n", len(comuns), f"Perguntas comparadas na {o_que}"),
            ]
    return lista


class RodadaSemParametros(RuntimeError):
    pass


def _numeros_dos_parametros(principal: Path) -> list[Numero | Texto]:
    """Os parâmetros com que a Rodada principal rodou, lidos do execucao.json gravado ao lado dela.

    Entram no registro para o Relatório de avaliação citá-los sem digitar: o k
    e os nomes dos modelos e do commit, que têm dígitos. São os da Rodada, e
    não os do parametros.toml de agora, que pode ter mudado depois dela.
    Sem execucao.json com parâmetros, a análise para aqui, antes de gravar
    qualquer coisa: o Relatório de avaliação cita esses parâmetros, e a
    compilação quebraria adiante com uma macro indefinida.
    """
    execucao = principal / "execucao.json"
    dados = json.loads(execucao.read_text(encoding="utf-8")) if execucao.exists() else {}
    p = dados.get("parametros")
    if not p:
        raise RodadaSemParametros(
            f"{execucao} não traz os parametros com que a Rodada principal rodou (k, modelos): "
            "rode de novo scripts/03_rodar_avaliacao.py --rodada principal, que os grava ao lado da Rodada"
        )
    juizes = _modelos_que_julgaram(principal) or [p["modelo_juiz"]]
    commit = dados["commit"]
    commit = commit[:7] if re.fullmatch(r"[0-9a-f]{40}", commit) else commit
    return [
        Numero("parametros_k", p["k"], "Trechos recuperados por Pergunta na Condição com RAG (Rodada principal)"),
        Texto("parametros_modelo_respondedor", p["modelo_respondedor"], p["modelo_respondedor"],
              "modelo que responde às Perguntas na Rodada principal"),
        Texto("parametros_modelo_juiz", juntar(juizes), juntar(juizes, "and"),
              "modelo(s) que julgaram na Rodada principal (a cadeia do Juiz, na ordem de uso)"),
        Texto("parametros_commit", commit, commit,
              "commit em que a Rodada principal rodou, com os parâmetros congelados"),
    ]


def _modelos_que_julgaram(principal: Path) -> list[str]:
    """Os modelos que de fato julgaram na Rodada principal, na ordem em que entraram.

    No plano gratuito o Juiz é uma cadeia de modelos (ADR 0005): quando a cota
    diária de um acaba, o seguinte assume. Linhas sem `modelo_juiz` (Rodadas
    anteriores à cadeia, ou sem Veredicto do Juiz) não contam.
    """
    vistos: list[str] = []
    for c in CONDICOES:
        for l in carregar_linhas(principal / f"{c}.jsonl"):
            m = l.get("modelo_juiz") or ""
            if m and m not in vistos:
                vistos.append(m)
    return vistos


def _textos_da_origem(principal: Path) -> list[Texto]:
    """De onde vêm as Rodadas, para a capa do Relatório de avaliação e o topo do README.

    Sobre Rodadas sintéticas, o aviso diz que os números são inventados; sobre
    as reais, ele é vazio e não aparece. A origem, na capa, só diz que os
    Veredictos do Juiz foram revisados quando a Rodada é real (a análise já
    recusou qualquer Veredicto sem Revisão).
    """
    if rodada_sintetica(principal):
        aviso = ("Atenção: os números deste documento saem de Rodadas sintéticas de demonstração e são "
                 "inventados; não são resultado do assistente.",
                 "Warning: the numbers in this document come from synthetic demo runs and are made up; "
                 "they are not results of the assistant.")
        origem = ("Rodadas sintéticas de demonstração, com números inventados",
                  "Synthetic demo runs, with made-up numbers")
    else:
        aviso = ("", "")
        origem = ("Rodada principal, com os Veredictos do Juiz revisados pelo autor",
                  "Main run, with the Judge's verdicts reviewed by the author")
    return [
        Texto("aviso_sintetico", *aviso, "aviso de números inventados, só sobre Rodadas sintéticas (senão, vazio)"),
        Texto("rodadas_origem", *origem, "de onde vêm as Rodadas analisadas, para a capa"),
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


# --------------------------------------------------------------------------
# Linhas das tabelas do Relatório de avaliação
# --------------------------------------------------------------------------

class _Celulas:
    """Devolve o texto de uma chave escapado para o LaTeX e anota quais chaves a tabela usou."""

    def __init__(self, textos: dict[str, str]):
        self.textos = textos
        self.usadas: list[str] = []

    def __call__(self, chave: str) -> str:
        if chave not in self.usadas:
            self.usadas.append(chave)
        return texto_tex(self.textos[chave])

    def com_ic(self, chave: str) -> str:
        """"80,0\\% (67,0\\% a 88,8\\%)": o valor e o IC."""
        return f"{self(chave)} ({self(chave + '_inf')} a {self(chave + '_sup')})"


def _arquivo(colunas: str, linhas: list[list[str]]) -> str:
    cabecalho = [
        f"% GERADO por {SCRIPT}. Não edite à mão: rode o script de novo.",
        f"% Colunas: {colunas}.",
    ]
    return "\n".join(cabecalho + [" & ".join(celulas) + r" \\" for celulas in linhas]) + "\n"


def _montar_tabelas(textos: dict[str, str]) -> dict[str, tuple[str, list[str]]]:
    """nome do arquivo -> (conteúdo, chaves do registro usadas nele)."""
    tabelas: dict[str, tuple[str, list[str]]] = {}

    t = _Celulas(textos)
    linhas = []
    for c in CONDICOES:
        linhas.append([
            rotulo_condicao(c),
            t.com_ic(f"{c}_acerto_resposta"),
            t.com_ic(f"{c}_acerto_citacao"),
            t.com_ic(f"{c}_acerto_recuperacao") if f"{c}_acerto_recuperacao" in textos else "---",
            t.com_ic(f"{c}_abstencao_correta") if f"{c}_abstencao_correta" in textos else "---",
        ])
    tabelas["resultados_por_condicao.tex"] = (_arquivo(
        "Condição; Acerto da resposta; Acerto da citação; Acerto da recuperação (respondíveis); "
        f"Abstenção correta (sem resposta); cada medida com o IC de Wilson de {_nivel()}%", linhas), t.usadas)

    t = _Celulas(textos)
    linhas = []
    for outra in COMPARADAS_COM_RAG:
        k = f"com_rag_x_{outra}"
        linhas.append([
            f"Com RAG $\\times$ {NOMES_CONDICAO[outra]}",
            t(f"{k}_ambos"), t(f"{k}_so_com_rag"), t(f"{k}_so_{outra}"), t(f"{k}_nenhum"),
            f"{t(f'{k}_diferenca')} ({t(f'{k}_diferenca_inf')} a {t(f'{k}_diferenca_sup')})",
            t(f"{k}_p_mcnemar"),
        ])
    tabelas["comparacao_pareada.tex"] = (_arquivo(
        "Comparação; as duas acertam; só com RAG acerta; só a outra acerta; as duas erram; "
        f"diferença com RAG menos a outra (IC de Newcombe de {_nivel()}%); valor-p do McNemar exato", linhas), t.usadas)

    t = _Celulas(textos)
    linhas = []
    for tipo in TIPOS_RESPONDIVEIS:
        linhas.append([NOMES_TIPO[tipo], t(chave_por_tipo(tipo, "n")), t(chave_por_tipo(tipo, "acertos")),
                       *[t(chave_por_tipo(tipo, s)) for s in CLASSES_DAS_RESPONDIVEIS], "---"])
    linhas.append([NOMES_TIPO["sem_resposta"], t(chave_por_tipo("sem_resposta", "n")),
                   t(chave_por_tipo("sem_resposta", "acertos")), *["---"] * len(CLASSES_DAS_RESPONDIVEIS),
                   t(chave_por_tipo("sem_resposta", SO_NAS_SEM_RESPOSTA))])
    tabelas["erros_por_tipo.tex"] = (_arquivo(
        "Tipo de pergunta; n; acertos (nas sem resposta, abstenções corretas); falha de recuperação; "
        "falha de leitura; abstenção indevida; citação errada; resposta inventada; Condição com RAG", linhas),
        t.usadas)

    t = _Celulas(textos)
    linhas = [[rotulo_condicao(c), t(f"{c}_tokens_entrada_medio"), t(f"{c}_latencia_mediana_s"),
               t(f"{c}_n_fallback")] for c in CONDICOES]
    tabelas["custo_por_condicao.tex"] = (_arquivo(
        "Condição; tokens de entrada (média por Pergunta); latência mediana (s); respostas com fallback",
        linhas), t.usadas)

    # Uma linha por repetição e Condição que existir: o .tex não fixa quantas repetições houve.
    t = _Celulas(textos)
    linhas = [[NOMES_REPETICAO[rodada], rotulo_condicao(c), t(f"concordancia_{rodada}_{c}"),
               t(f"concordancia_{rodada}_{c}_n")]
              for rodada in REPETICOES for c in CONDICOES if f"concordancia_{rodada}_{c}" in textos]
    tabelas["concordancia.tex"] = (_arquivo(
        "Repetição; Condição; concordância dos Veredictos automáticos com a Rodada principal (não revisados); "
        "Perguntas comparadas", linhas), t.usadas)
    return tabelas


def analisar(
    pasta_rodadas: Path,
    folha: Path,
    numeros_json: Path | None = None,
    pasta_tabelas: Path | None = None,
) -> dict[str, str]:
    """Registra os números da Rodada principal e devolve chave -> texto formatado."""
    pasta_rodadas = Path(pasta_rodadas)
    numeros_json = Path(numeros_json or config.NUMEROS)
    pasta_tabelas = Path(pasta_tabelas or config.TABELAS)
    recusar_no_projeto(pasta_rodadas, numeros_json, pasta_tabelas, passo="a análise")
    consolidadas = _consolidar_principal(pasta_rodadas / "principal", folha)
    resumos = {c: resumir(consolidadas[c]) for c in CONDICOES}
    lista: list[Numero | Texto] = (
        [Numero("ic_nivel", _nivel(), "nível de confiança dos intervalos de Wilson e de Newcombe, em %")]
        + _numeros_de_destaque(resumos)
        + _numeros_do_gabarito(consolidadas["com_rag"])
        + _numeros_da_rodada(resumos)
        + _numeros_da_revisao(consolidadas)
        + _numeros_dos_parametros(pasta_rodadas / "principal")
        + _textos_da_origem(pasta_rodadas / "principal")
    )
    for c in CONDICOES:
        lista += _numeros_da_condicao(c, resumos[c]) + _numeros_dos_erros(c, resumos[c])
    lista += _numeros_do_erro_mais_frequente("com_rag", resumos["com_rag"])
    lista += _numeros_por_tipo(consolidadas["com_rag"])
    for outra in COMPARADAS_COM_RAG:
        lista += _numeros_da_comparacao(outra, consolidadas["com_rag"], consolidadas[outra])
    lista += _numeros_da_concordancia(pasta_rodadas)

    textos = {n.chave: numeros.formatar(n.valor, n.formato or "inteiro") for n in lista if isinstance(n, Numero)}
    tabelas = _montar_tabelas(textos)
    onde: dict[str, list[str]] = {}
    for nome, (_, usadas) in tabelas.items():
        for chave in usadas:
            onde.setdefault(chave, []).append(f"{TABELAS_NO_PROJETO}/{nome}")
    lista = [replace(n, aparece_em=tuple(onde.get(n.chave, ()))) if isinstance(n, Numero) else n for n in lista]

    registrados = numeros.registrar_do_script(SCRIPT, lista, caminho=numeros_json)
    pasta_tabelas.mkdir(parents=True, exist_ok=True)
    for nome, (conteudo, _) in tabelas.items():
        (pasta_tabelas / nome).write_text(conteudo, encoding="utf-8", newline="\n")
    return registrados

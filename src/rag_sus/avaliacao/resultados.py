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

from dataclasses import replace
from pathlib import Path

from rag_sus import config, numeros
from rag_sus.assistente import CONDICOES
from rag_sus.avaliacao.analise import comparar, concordancia, erros_por_tipo, resumir
from rag_sus.avaliacao.gabarito import TIPOS_RESPONDIVEIS
from rag_sus.avaliacao.rodada import RevisaoIncompleta, carregar_linhas, consolidar
from rag_sus.avaliacao.travas import RODADAS_PUBLICADAS
from rag_sus.documentos import texto_tex
from rag_sus.numeros import Numero

REPETICOES = tuple(r for r in RODADAS_PUBLICADAS if r != "principal")

SCRIPT = "scripts/04_analisar.py"
TABELAS_NO_PROJETO = "relatorio/tabelas"  # como a coluna "Onde aparece" cita os arquivos de linhas
NOMES_CONDICAO = {"com_rag": "com RAG", "sem_rag": "sem RAG", "contexto_completo": "contexto completo"}
NOMES_TIPO = {
    "numero_prosa": "Número na prosa",
    "numero_tabela": "Número em tabela",
    "numero_legenda": "Número em legenda",
    "conceito": "Conceito ou método",
    "sintese": "Síntese entre páginas",
    "sem_resposta": "Sem resposta",
}
# Classe de erro (como sai de pontuacao.classificar_erro) -> pedaço da chave no registro.
CLASSES_DE_ERRO = {
    "falha de recuperação": "falha_recuperacao",
    "falha de leitura": "falha_leitura",
    "abstenção indevida": "abstencao_indevida",
    "citação errada": "citacao_errada",
    "resposta inventada": "resposta_inventada",
}
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
        Numero(f"{c}_erros_{slug}", r["erros"].get(classe, 0), f"Classe de erro '{classe}' {nome} (Perguntas)")
        for classe, slug in CLASSES_DE_ERRO.items()
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
            Numero(f"com_rag_tipo_{tipo}_n", celula.get("n", 0), f"Perguntas do Tipo '{nome}'"),
            Numero(f"com_rag_tipo_{tipo}_acertos", acertos, f"acertos da resposta com RAG, Tipo '{nome}'"),
        ]
        lista += [
            Numero(f"com_rag_tipo_{tipo}_{slug}", celula.get(classe, 0), f"'{classe}' com RAG, Tipo '{nome}'")
            for classe, slug in CLASSES_DE_ERRO.items()
            if classe != "resposta inventada"
        ]
    sem = [l for l in linhas if not l["respondivel"]]
    lista += [
        Numero("com_rag_tipo_sem_resposta_n", len(sem), "Perguntas sem resposta"),
        Numero("com_rag_tipo_sem_resposta_acertos", sum(l["acerto_resposta"] for l in sem),
               "abstenções corretas com RAG nas Perguntas sem resposta"),
        Numero("com_rag_tipo_sem_resposta_resposta_inventada",
               sum(l["classe_erro"] == "resposta inventada" for l in sem),
               "'resposta inventada' com RAG nas Perguntas sem resposta"),
    ]
    return lista


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


def _numeros_da_concordancia(pasta_rodadas: Path) -> list[Numero]:
    """Concordância entre a Rodada principal e cada repetição que existir, por Condição.

    Compara os Veredictos automáticos (Juiz ou regra), sem a Revisão: as
    repetições não são revisadas, e a principal entra do mesmo jeito para a
    comparação ser justa.
    """
    lista: list[Numero] = []
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
        """"80,0\\% (67,0\\% a 88,8\\%)": o valor e o IC de 95%."""
        return f"{self(chave)} ({self(chave + '_inf')} a {self(chave + '_sup')})"


def _rotulo(condicao: str) -> str:
    """"com RAG" -> "Com RAG", para abrir a linha da tabela."""
    nome = NOMES_CONDICAO[condicao]
    return nome[:1].upper() + nome[1:]


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
            _rotulo(c),
            t.com_ic(f"{c}_acerto_resposta"),
            t.com_ic(f"{c}_acerto_citacao"),
            t.com_ic(f"{c}_acerto_recuperacao") if f"{c}_acerto_recuperacao" in textos else "---",
            t.com_ic(f"{c}_abstencao_correta") if f"{c}_abstencao_correta" in textos else "---",
        ])
    tabelas["resultados_por_condicao.tex"] = (_arquivo(
        "Condição; Acerto da resposta; Acerto da citação; Acerto da recuperação (respondíveis); "
        "Abstenção correta (sem resposta); cada medida com o IC de Wilson de 95%", linhas), t.usadas)

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
        "diferença com RAG menos a outra (IC de Newcombe de 95%); valor-p do McNemar exato", linhas), t.usadas)

    t = _Celulas(textos)
    linhas = []
    classes_respondiveis = [s for s in CLASSES_DE_ERRO.values() if s != "resposta_inventada"]
    for tipo in TIPOS_RESPONDIVEIS:
        k = f"com_rag_tipo_{tipo}"
        linhas.append([NOMES_TIPO[tipo], t(f"{k}_n"), t(f"{k}_acertos"),
                       *[t(f"{k}_{s}") for s in classes_respondiveis], "---"])
    k = "com_rag_tipo_sem_resposta"
    linhas.append([NOMES_TIPO["sem_resposta"], t(f"{k}_n"), t(f"{k}_acertos"),
                   *["---"] * len(classes_respondiveis), t(f"{k}_resposta_inventada")])
    tabelas["erros_por_tipo.tex"] = (_arquivo(
        "Tipo de pergunta; n; acertos (nas sem resposta, abstenções corretas); falha de recuperação; "
        "falha de leitura; abstenção indevida; citação errada; resposta inventada; Condição com RAG", linhas),
        t.usadas)

    t = _Celulas(textos)
    linhas = [[_rotulo(c), t(f"{c}_tokens_entrada_medio"), t(f"{c}_latencia_mediana_s"),
               t(f"{c}_n_fallback")] for c in CONDICOES]
    tabelas["custo_por_condicao.tex"] = (_arquivo(
        "Condição; tokens de entrada (média por Pergunta); latência mediana (s); respostas com fallback",
        linhas), t.usadas)
    return tabelas


def analisar(
    pasta_rodadas: Path,
    folha: Path,
    numeros_json: Path | None = None,
    pasta_tabelas: Path | None = None,
) -> dict[str, str]:
    """Registra os números da Rodada principal e devolve chave -> texto formatado."""
    pasta_rodadas = Path(pasta_rodadas)
    consolidadas = _consolidar_principal(pasta_rodadas / "principal", folha)
    resumos = {c: resumir(consolidadas[c]) for c in CONDICOES}
    lista: list[Numero] = (
        _numeros_de_destaque(resumos) + _numeros_da_rodada(resumos) + _numeros_da_revisao(consolidadas)
    )
    for c in CONDICOES:
        lista += _numeros_da_condicao(c, resumos[c]) + _numeros_dos_erros(c, resumos[c])
    lista += _numeros_por_tipo(consolidadas["com_rag"])
    for outra in COMPARADAS_COM_RAG:
        lista += _numeros_da_comparacao(outra, consolidadas["com_rag"], consolidadas[outra])
    lista += _numeros_da_concordancia(pasta_rodadas)

    textos = {n.chave: numeros.formatar(n.valor, n.formato or "inteiro") for n in lista}
    tabelas = _montar_tabelas(textos)
    onde: dict[str, list[str]] = {}
    for nome, (_, usadas) in tabelas.items():
        for chave in usadas:
            onde.setdefault(chave, []).append(f"{TABELAS_NO_PROJETO}/{nome}")
    lista = [replace(n, aparece_em=tuple(onde.get(n.chave, ()))) for n in lista]

    registrados = numeros.registrar_do_script(SCRIPT, lista, caminho=numeros_json or config.NUMEROS)
    pasta_tabelas = Path(pasta_tabelas or config.TABELAS)
    pasta_tabelas.mkdir(parents=True, exist_ok=True)
    for nome, (conteudo, _) in tabelas.items():
        (pasta_tabelas / nome).write_text(conteudo, encoding="utf-8", newline="\n")
    return registrados

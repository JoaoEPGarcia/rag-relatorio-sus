# -*- coding: utf-8 -*-
"""Provedores de modelo de linguagem: Gemini (plano gratuito) e Ollama (local).

POR QUE ISTO EXISTE. O assistente e o Juiz pedem a mesma coisa a um modelo:
um prompt de sistema, uma mensagem e um esquema JSON de saída. Isolar o
provedor aqui deixa trocar a API do Gemini por um modelo local (Ollama) sem
tocar no resto. Os números publicados saem do Gemini (ADR 0005), no plano
gratuito do Google AI Studio ou num projeto pré-pago com os créditos mensais
do Google AI Pro. O Ollama serve para usar o assistente sem internet.

A cota vale por minuto e por dia, por projeto e por modelo. Quando a cota por
minuto estoura, o provedor espera o tempo que a própria API indica e tenta de
novo. Quando a cota diária acaba (`CotaDiariaEsgotada`) ou o saldo pré-pago
zera (`SaldoEsgotado`), ele para, e a Rodada, que é retomável, continua de
onde parou quando a cota renovar.

Cada chamada devolve também os metadados que a avaliação precisa: o modelo
que de fato respondeu, os tokens e a latência. Como não há fatura, o custo de
cada Condição é medido em tokens.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Protocol

import httpx

URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta"
# Uma resposta normal leva segundos (a mais lenta da Rodada de desenvolvimento,
# com o Relatório-fonte inteiro no prompt, levou menos de 20 s). Quatro minutos
# sem resposta é modelo preso, e a requisição é tentada de novo.
TEMPO_LIMITE_S = 240


@dataclass
class Metadados:
    modelo_pedido: str
    modelo_que_respondeu: str
    usou_fallback: bool
    tokens_entrada: int = 0
    tokens_saida: int = 0
    tokens_cache_escrita: int = 0
    tokens_cache_leitura: int = 0
    latencia_s: float = 0.0
    motivo_parada: str = ""
    id_requisicao: str = ""
    extras: dict = field(default_factory=dict)

    @property
    def custo_usd(self) -> float:
        # Não é estimado em dólar: no plano gratuito e no Ollama é zero, e no
        # projeto pré-pago quem paga são os créditos do AI Pro (ADR 0005). O
        # custo de cada Condição é medido em tokens.
        return 0.0


class RecusaDoModelo(RuntimeError):
    """O modelo recusou ou bloqueou a resposta por um filtro de segurança."""


class CotaEsgotada(RuntimeError):
    """O Gemini parou de aceitar chamadas até a cota renovar ou o saldo voltar."""


class CotaDiariaEsgotada(CotaEsgotada):
    """A cota diária do projeto acabou; ela renova à meia-noite do Pacífico."""


class SaldoEsgotado(CotaEsgotada):
    """O saldo pré-pago do faturamento (créditos do Google AI Pro + pré-pagamento) zerou.

    É o teto de gasto do projeto: com Prepay e sem recarga automática, a API
    devolve 402 e nada mais é cobrado (ADR 0005).
    """


class ModeloIndisponivel(RuntimeError):
    """O modelo não respondeu (tempo esgotado ou sobrecarga) em nenhuma das tentativas.

    Acontece no plano gratuito: um modelo às vezes fica sem responder por
    muito tempo. A Rodada para (o respondedor) ou passa ao reserva seguinte (o
    Juiz em cadeia), e o mesmo comando retoma depois.
    """


class Provedor(Protocol):
    nome: str

    def gerar_json(
        self, sistema: list[dict], mensagem: str, esquema: dict
    ) -> tuple[dict, Metadados]: ...


# Motivos de parada do Gemini que indicam bloqueio, e não uma resposta.
_MOTIVOS_DE_BLOQUEIO = {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "LANGUAGE"}


def _espera_sugerida(corpo: dict) -> float | None:
    """Lê o RetryInfo (ex.: "41s") que a API manda junto com o erro 429."""
    for d in corpo.get("error", {}).get("details", []):
        m = re.match(r"([\d.]+)s", d.get("retryDelay", ""))
        if m:
            return float(m.group(1))
    return None


def _cota_diaria(corpo: dict) -> bool:
    for d in corpo.get("error", {}).get("details", []):
        for v in d.get("violations", []):
            if "PerDay" in v.get("quotaId", "") or "per_day" in v.get("quotaMetric", ""):
                return True
    return False


class ProvedorGemini:
    """Gemini pela API REST, com saída estruturada por JSON Schema.

    `esforco` vira o nível de raciocínio (thinkingLevel: low, medium ou high).
    Um prefixo que se repete entre chamadas (o texto inteiro do Relatório-fonte,
    na Condição contexto completo) entra no cache implícito do Gemini, e os
    tokens lidos do cache ficam em `tokens_cache_leitura`.
    """

    nome = "gemini"

    def __init__(self, modelo: str, esforco: str, max_tokens: int, chave: str | None = None,
                 cliente: httpx.Client | None = None, tentativas: int = 6, dormir=time.sleep,
                 relogio=time.perf_counter):
        chave = chave or os.environ.get("GEMINI_API_KEY", "")
        if not chave and cliente is None:
            raise RuntimeError("GEMINI_API_KEY não está no ambiente nem no .env")
        self.modelo = modelo
        self.esforco = esforco
        self.max_tokens = max_tokens
        self.tentativas = tentativas
        self._dormir = dormir
        self._relogio = relogio
        self._http = cliente or httpx.Client(
            base_url=URL_GEMINI, headers={"x-goog-api-key": chave}, timeout=TEMPO_LIMITE_S
        )

    def _post(self, corpo: dict) -> tuple[httpx.Response, float]:
        """Devolve a resposta e a latência só da requisição que deu certo.

        As esperas por cota (429), por sobrecarga (5xx) e por tempo esgotado não
        entram na latência, que é comparada entre Condições. Sobrecarga e tempo
        esgotado em todas as tentativas viram `ModeloIndisponivel`.
        """
        espera = 5.0
        for tentativa in range(1, self.tentativas + 1):
            inicio = self._relogio()
            try:
                r = self._http.post(f"/models/{self.modelo}:generateContent", json=corpo)
            except httpx.TransportError as erro:  # tempo esgotado ou conexão caída
                if tentativa == self.tentativas:
                    raise ModeloIndisponivel(
                        f"{self.modelo} não respondeu em {self.tentativas} tentativas ({type(erro).__name__})"
                    ) from erro
                self._dormir(espera + 1)
                espera = min(espera * 2, 120)
                continue
            latencia = self._relogio() - inicio
            if r.status_code == 402:
                raise SaldoEsgotado(
                    "o saldo pré-pago do faturamento zerou (créditos do Google AI Pro e pré-pagamento); "
                    "a API volta quando houver saldo ou créditos novos"
                )
            if r.status_code == 429:
                erro = r.json()
                if _cota_diaria(erro):
                    raise CotaDiariaEsgotada(
                        f"cota diária do plano gratuito esgotada para {self.modelo}; "
                        "ela renova à meia-noite do Pacífico"
                    )
                pausa = _espera_sugerida(erro) or espera
            elif r.status_code in (500, 502, 503, 504):
                pausa = espera  # modelo sobrecarregado, comum no plano gratuito
                if tentativa == self.tentativas:
                    raise ModeloIndisponivel(
                        f"{self.modelo} sobrecarregado em {self.tentativas} tentativas (HTTP {r.status_code})"
                    )
            else:
                r.raise_for_status()
                return r, latencia
            if tentativa == self.tentativas:
                r.raise_for_status()
            self._dormir(pausa + 1)
            espera = min(espera * 2, 120)
        raise AssertionError("inalcançável")

    def gerar_json(self, sistema: list[dict], mensagem: str, esquema: dict) -> tuple[dict, Metadados]:
        corpo = {
            "systemInstruction": {"parts": [{"text": b["text"]} for b in sistema]},
            "contents": [{"role": "user", "parts": [{"text": mensagem}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": esquema,
                "maxOutputTokens": self.max_tokens,
                "thinkingConfig": {"thinkingLevel": self.esforco},
            },
        }
        r, latencia = self._post(corpo)
        resposta = r.json()

        uso = resposta.get("usageMetadata", {})
        candidatos = resposta.get("candidates") or [{}]
        motivo = candidatos[0].get("finishReason", "")
        respondeu = resposta.get("modelVersion", self.modelo)
        meta = Metadados(
            modelo_pedido=self.modelo,
            modelo_que_respondeu=respondeu,
            usou_fallback=not respondeu.startswith(self.modelo),
            tokens_entrada=uso.get("promptTokenCount", 0),
            tokens_saida=uso.get("candidatesTokenCount", 0) + uso.get("thoughtsTokenCount", 0),
            tokens_cache_leitura=uso.get("cachedContentTokenCount", 0),
            latencia_s=latencia,
            motivo_parada=motivo,
            id_requisicao=resposta.get("responseId", ""),
        )
        bloqueio = resposta.get("promptFeedback", {}).get("blockReason")
        if bloqueio or motivo in _MOTIVOS_DE_BLOQUEIO:
            raise RecusaDoModelo(f"bloqueio do modelo: {bloqueio or motivo} ({meta.id_requisicao})")
        if motivo == "MAX_TOKENS":
            raise RuntimeError(f"resposta cortada em maxOutputTokens ({meta.id_requisicao})")
        partes = candidatos[0].get("content", {}).get("parts", [])
        texto = "".join(p.get("text", "") for p in partes if not p.get("thought"))
        return json.loads(texto), meta


class ProvedorOllama:
    """Modelo local via Ollama: sem custo e sem cota, mas não gera números publicados."""

    nome = "ollama"

    def __init__(self, modelo: str, url: str = "http://localhost:11434", tempo_limite: float = 600):
        self.modelo = modelo
        self._http = httpx.Client(base_url=url, timeout=tempo_limite)

    def gerar_json(self, sistema: list[dict], mensagem: str, esquema: dict) -> tuple[dict, Metadados]:
        inicio = time.perf_counter()
        r = self._http.post(
            "/api/chat",
            json={
                "model": self.modelo,
                "stream": False,
                "format": esquema,
                "options": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": "\n\n".join(b["text"] for b in sistema)},
                    {"role": "user", "content": mensagem},
                ],
            },
        )
        r.raise_for_status()
        corpo = r.json()
        meta = Metadados(
            modelo_pedido=self.modelo,
            modelo_que_respondeu=corpo.get("model", self.modelo),
            usou_fallback=False,
            tokens_entrada=corpo.get("prompt_eval_count", 0),
            tokens_saida=corpo.get("eval_count", 0),
            latencia_s=time.perf_counter() - inicio,
            motivo_parada=corpo.get("done_reason", ""),
        )
        return json.loads(corpo["message"]["content"]), meta


class ProvedorEmCadeia:
    """Vários modelos em ordem: quando a cota diária de um acaba, o seguinte assume.

    Também passa ao seguinte quando o atual não responde (`ModeloIndisponivel`).
    Serve só ao Juiz (ADR 0005). No plano gratuito a cota é por modelo, e somar
    a de vários modelos é o que faz a Rodada caber em poucos dias. O
    respondedor não usa cadeia: trocar o modelo no meio misturaria dois
    sistemas na comparação entre Condições. O Juiz pode trocar, porque todo
    Veredicto dele passa pela Revisão do autor, e cada linha da Rodada
    registra o modelo que julgou. Um modelo esgotado não é chamado de novo
    nesta execução.
    """

    nome = "cadeia"

    def __init__(self, provedores: list[Provedor]):
        self.provedores = list(provedores)
        self._atual = 0

    def gerar_json(self, sistema: list[dict], mensagem: str, esquema: dict) -> tuple[dict, Metadados]:
        while self._atual < len(self.provedores):
            try:
                return self.provedores[self._atual].gerar_json(sistema, mensagem, esquema)
            except (CotaDiariaEsgotada, ModeloIndisponivel):
                self._atual += 1
        modelos = ", ".join(p.modelo for p in self.provedores)
        raise CotaDiariaEsgotada(f"cota diária esgotada ou modelo indisponível em todos os modelos da cadeia ({modelos})")


def provedor_do_ambiente(modelo: str, esforco: str, max_tokens: int) -> Provedor:
    """Escolhe o provedor pela variável PROVEDOR do .env (padrão: gemini)."""
    if os.environ.get("PROVEDOR", "gemini") == "ollama":
        return ProvedorOllama(
            os.environ.get("OLLAMA_MODELO", "qwen2.5:7b"),
            os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        )
    return ProvedorGemini(modelo, esforco, max_tokens)


def juiz_do_ambiente(modelos: list[str], esforco: str, max_tokens: int) -> Provedor:
    """O Juiz: o primeiro modelo, seguido dos reservas, em cadeia (só no Gemini).

    No Ollama não há cota, e o modelo local é um só.
    """
    if os.environ.get("PROVEDOR", "gemini") == "ollama" or len(modelos) == 1:
        return provedor_do_ambiente(modelos[0], esforco, max_tokens)
    return ProvedorEmCadeia([ProvedorGemini(m, esforco, max_tokens) for m in modelos])

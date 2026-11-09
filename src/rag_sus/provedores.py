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
                 cliente: httpx.Client | None = None, tentativas: int = 6, dormir=time.sleep):
        chave = chave or os.environ.get("GEMINI_API_KEY", "")
        if not chave and cliente is None:
            raise RuntimeError("GEMINI_API_KEY não está no ambiente nem no .env")
        self.modelo = modelo
        self.esforco = esforco
        self.max_tokens = max_tokens
        self.tentativas = tentativas
        self._dormir = dormir
        self._http = cliente or httpx.Client(
            base_url=URL_GEMINI, headers={"x-goog-api-key": chave}, timeout=600
        )

    def _post(self, corpo: dict) -> httpx.Response:
        espera = 5.0
        for tentativa in range(1, self.tentativas + 1):
            r = self._http.post(f"/models/{self.modelo}:generateContent", json=corpo)
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
            else:
                r.raise_for_status()
                return r
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
        inicio = time.perf_counter()
        resposta = self._post(corpo).json()
        latencia = time.perf_counter() - inicio

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


def provedor_do_ambiente(modelo: str, esforco: str, max_tokens: int) -> Provedor:
    """Escolhe o provedor pela variável PROVEDOR do .env (padrão: gemini)."""
    if os.environ.get("PROVEDOR", "gemini") == "ollama":
        return ProvedorOllama(
            os.environ.get("OLLAMA_MODELO", "qwen2.5:7b"),
            os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        )
    return ProvedorGemini(modelo, esforco, max_tokens)

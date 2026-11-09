# -*- coding: utf-8 -*-
"""Provedores de modelo de linguagem: Anthropic (números publicados) e Ollama.

POR QUE ISTO EXISTE. O assistente e o Juiz pedem a mesma coisa a um modelo:
um prompt de sistema, uma mensagem e um esquema JSON de saída. Isolar o
provedor aqui deixa trocar a API da Anthropic por um modelo local (Ollama)
sem tocar no resto. Os números publicados saem só do provedor Anthropic
(docs/DESENHO.md); o Ollama existe para quem quiser rodar sem custo.

Cada chamada devolve também os metadados que a avaliação precisa: o modelo
que de fato respondeu (o fallback do servidor pode trocar o modelo quando o
principal recusa por um filtro de segurança), os tokens e a latência.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Protocol

# Preço por milhão de tokens (US$), da tabela da skill claude-api em
# 06/10/2026. Usado só para estimar custo por Pergunta; a fatura é a fonte.
PRECOS_POR_MILHAO = {
    "claude-opus-5-5": {"entrada": 4.00, "saida": 20.00, "cache_escrita": 5.00, "cache_leitura": 0.20},
}


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
    def custo_usd(self) -> float | None:
        preco = PRECOS_POR_MILHAO.get(self.modelo_que_respondeu)
        if preco is None:
            return None
        return (
            self.tokens_entrada * preco["entrada"]
            + self.tokens_saida * preco["saida"]
            + self.tokens_cache_escrita * preco["cache_escrita"]
            + self.tokens_cache_leitura * preco["cache_leitura"]
        ) / 1_000_000


class RecusaDoModelo(RuntimeError):
    """O modelo (e o fallback) recusaram por um filtro de segurança."""


class Provedor(Protocol):
    nome: str

    def gerar_json(
        self, sistema: list[dict], mensagem: str, esquema: dict
    ) -> tuple[dict, Metadados]: ...


class ProvedorAnthropic:
    """Claude via SDK oficial, com saída estruturada e fallback do servidor.

    `sistema` é uma lista de blocos de texto; o último recebe cache_control,
    de modo que um prompt longo e fixo (o texto inteiro do Relatório-fonte, na
    Condição contexto completo) seja lido do cache nas Perguntas seguintes.
    """

    nome = "anthropic"

    def __init__(self, modelo: str, esforco: str, max_tokens: int, cliente=None):
        import anthropic

        self.modelo = modelo
        self.esforco = esforco
        self.max_tokens = max_tokens
        self._cliente = cliente or anthropic.Anthropic()

    def gerar_json(self, sistema: list[dict], mensagem: str, esquema: dict) -> tuple[dict, Metadados]:
        blocos = [dict(b) for b in sistema]
        if blocos:
            blocos[-1]["cache_control"] = {"type": "ephemeral"}

        inicio = time.perf_counter()
        resposta = self._cliente.beta.messages.create(
            model=self.modelo,
            max_tokens=self.max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={
                "effort": self.esforco,
                "format": {"type": "json_schema", "schema": esquema},
            },
            system=blocos,
            messages=[{"role": "user", "content": mensagem}],
        )
        latencia = time.perf_counter() - inicio

        uso = resposta.usage
        usou_fallback = any(
            getattr(it, "type", "") == "fallback_message" for it in (getattr(uso, "iterations", None) or [])
        )
        meta = Metadados(
            modelo_pedido=self.modelo,
            modelo_que_respondeu=resposta.model,
            usou_fallback=usou_fallback or resposta.model != self.modelo,
            tokens_entrada=uso.input_tokens or 0,
            tokens_saida=uso.output_tokens or 0,
            tokens_cache_escrita=getattr(uso, "cache_creation_input_tokens", 0) or 0,
            tokens_cache_leitura=getattr(uso, "cache_read_input_tokens", 0) or 0,
            latencia_s=latencia,
            motivo_parada=resposta.stop_reason or "",
            id_requisicao=getattr(resposta, "_request_id", "") or "",
        )
        if resposta.stop_reason == "refusal":
            raise RecusaDoModelo(f"recusa do modelo ({meta.id_requisicao})")
        if resposta.stop_reason == "max_tokens":
            raise RuntimeError(f"resposta cortada em max_tokens ({meta.id_requisicao})")
        texto = next(b.text for b in resposta.content if b.type == "text")
        return json.loads(texto), meta


class ProvedorOllama:
    """Modelo local via Ollama (sem custo, sem números publicados)."""

    nome = "ollama"

    def __init__(self, modelo: str, url: str = "http://localhost:11434", tempo_limite: float = 600):
        import httpx

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
    """Escolhe o provedor pela variável PROVEDOR do .env (padrão: anthropic)."""
    import os

    if os.environ.get("PROVEDOR", "anthropic") == "ollama":
        return ProvedorOllama(
            os.environ.get("OLLAMA_MODELO", "qwen2.5:7b"),
            os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        )
    return ProvedorAnthropic(modelo, esforco, max_tokens)

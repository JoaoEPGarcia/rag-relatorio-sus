# -*- coding: utf-8 -*-
"""API HTTP do assistente (FastAPI).

POR QUE ISTO EXISTE. É a forma de usar o assistente fora da avaliação:
`POST /perguntar` recebe uma Pergunta e devolve a resposta, as páginas
citadas e os Trechos em que ela se apoiou, para quem pergunta conferir no
PDF. A documentação interativa fica em /docs (Swagger).

O assistente é montado uma vez, na subida do servidor (carregar o modelo de
embeddings leva alguns segundos). `criar_app` aceita um assistente pronto
para que os testes troquem o modelo e a API por falsos.

Uso: uv run uvicorn rag_sus.api:app --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rag_sus.assistente import Assistente


class PedidoPergunta(BaseModel):
    pergunta: str = Field(..., min_length=3, max_length=1000,
                          examples=["Quantas cirurgias os hospitais filantrópicos fizeram em 2025?"])


class TrechoCitado(BaseModel):
    id: str
    pagina: int
    tipo: str
    texto: str


class RespostaPergunta(BaseModel):
    resposta: str
    paginas_citadas: list[int]
    abstencao: bool
    trechos: list[TrechoCitado]
    modelo: str


def montar_assistente_padrao() -> Assistente:
    from rag_sus import config
    from rag_sus.busca import E5Embutidor, IndiceDeTrechos
    from rag_sus.provedores import provedor_do_ambiente

    config.carregar_env()
    p = config.carregar_parametros()
    embutidor = E5Embutidor(pasta_cache=config.CACHE_MODELOS)
    indice = IndiceDeTrechos.carregar(config.INDICE, embutidor)
    provedor = provedor_do_ambiente(p.modelo_respondedor, p.esforco_respondedor, p.max_tokens_respondedor)
    return Assistente(provedor, indice, embutidor, k=p.k)


def criar_app(assistente: Assistente | None = None) -> FastAPI:
    estado: dict = {"assistente": assistente}

    @asynccontextmanager
    async def ciclo_de_vida(_app: FastAPI):
        if estado["assistente"] is None:
            estado["assistente"] = montar_assistente_padrao()
        yield

    app = FastAPI(
        title="Assistente do relatório Gestão Hospitalar no SUS-SP",
        description="Responde perguntas sobre o relatório, citando a página impressa.",
        version="0.1.0",
        lifespan=ciclo_de_vida,
    )

    @app.get("/saude")
    def saude() -> dict:
        a = estado["assistente"]
        return {"status": "ok", "trechos_indexados": len(a.indice.trechos) if a and a.indice else 0}

    @app.post("/perguntar", response_model=RespostaPergunta)
    def perguntar(pedido: PedidoPergunta) -> RespostaPergunta:
        a: Assistente = estado["assistente"]
        try:
            r = a.responder(pedido.pergunta, "com_rag")
        except Exception as erro:  # a API não expõe detalhes internos
            raise HTTPException(
                status_code=502, detail=f"falha ao consultar o modelo: {type(erro).__name__}"
            ) from None
        por_id = {t.id: t for t in a.indice.trechos}
        trechos = [
            TrechoCitado(id=i, pagina=por_id[i].pagina_impressa, tipo=por_id[i].tipo, texto=por_id[i].texto)
            for i in r.trechos_recuperados
        ]
        return RespostaPergunta(
            resposta=r.resposta,
            paginas_citadas=list(r.paginas_citadas),
            abstencao=r.abstencao,
            trechos=trechos,
            modelo=r.metadados.modelo_que_respondeu if r.metadados else "",
        )

    return app


app = criar_app()

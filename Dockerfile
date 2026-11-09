# Imagem da API do assistente.
#
# O modelo de embeddings (2,24 GB) e o índice NÃO vão para a imagem: ficam em
# volumes (ver docker-compose.yml) e são criados na primeira subida por
# scripts/iniciar_api.sh. Assim a imagem leva só o código e os Trechos.

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    RAG_SUS_RAIZ=/app \
    RAG_SUS_CACHE_MODELOS=/app/modelos

# Dependências primeiro, para o cache de camadas não refazê-las a cada mudança no código.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY scripts ./scripts
COPY parametros.toml ./
COPY dados/trechos.jsonl ./dados/trechos.jsonl
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["sh", "scripts/iniciar_api.sh"]

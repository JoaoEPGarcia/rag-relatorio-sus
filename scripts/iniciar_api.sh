#!/bin/sh
# Sobe a API dentro do contêiner. Na primeira vez, constrói o índice (baixa o
# modelo de embeddings para o volume modelos/ e calcula os vetores dos Trechos).
set -e

if [ ! -f indice/meta.json ]; then
    echo "Índice ausente: construindo (primeira subida; leva alguns minutos)..."
    uv run --no-dev python scripts/02_indexar.py
fi

exec uv run --no-dev uvicorn rag_sus.api:app --host 0.0.0.0 --port 8000

# -*- coding: utf-8 -*-
"""Confere a chave do Gemini sem gastar cota: lista os modelos disponíveis.

POR QUE ISTO EXISTE. O wizard (scripts/configurar_maquina.sh) grava a chave no
.env e precisa saber se ela funciona antes de qualquer Rodada. Listar os
modelos não conta na cota de geração e confirma, de uma vez, que a chave é
válida e que os modelos dos parâmetros (respondedor e Juiz) estão disponíveis.

Uso: uv run python scripts/conferir_chave.py  (lê GEMINI_API_KEY do ambiente ou do .env)
"""

import os
import sys

import httpx

from rag_sus import config
from rag_sus.provedores import URL_GEMINI


def main() -> int:
    config.carregar_env()
    p = config.carregar_parametros()
    chave = os.environ.get("GEMINI_API_KEY", "")
    if not chave:
        print("GEMINI_API_KEY não está no .env.")
        return 1

    ids, pagina = set(), None
    with httpx.Client(base_url=URL_GEMINI, headers={"x-goog-api-key": chave}, timeout=60) as http:
        while True:
            r = http.get("/models", params={"pageSize": 1000, **({"pageToken": pagina} if pagina else {})})
            if r.status_code in (400, 401, 403):
                print("Chave inválida.")
                return 1
            if r.is_error:
                print(f"Falha ao consultar a API: HTTP {r.status_code}")
                return 1
            corpo = r.json()
            ids |= {m["name"].removeprefix("models/") for m in corpo.get("models", [])}
            pagina = corpo.get("nextPageToken")
            if not pagina:
                break

    faltando = sorted({p.modelo_respondedor, p.modelo_juiz} - ids)
    if faltando:
        print(f"A chave funciona, mas estes modelos não aparecem para ela: {', '.join(faltando)}")
        return 1
    print(f"Chave válida; {p.modelo_respondedor} e {p.modelo_juiz} disponíveis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

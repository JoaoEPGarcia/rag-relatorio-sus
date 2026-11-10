# 06: Chave da API e Docker Desktop

**What to build:** o autor deixa a máquina pronta para as Rodadas e para subir a API em contêiner. Ele cria a chave do Gemini no Google AI Studio, na conta do Google AI Pro, e grava em `.env`. Se quiser os créditos mensais do AI Pro, vincula o plano ao Google Developer Program e liga o faturamento Prepay (mínimo de US$ 5, recarga automática desligada) no projeto da chave (ADR 0005); senão, fica no plano gratuito. Ele também anota a cota diária do `gemini-3.8-flash` que o AI Studio mostra (copiado de `.env.exemplo`, fora do git), e instala o Docker Desktop. É o passo 2.W do plano: o roteiro do wizard guia cada tela.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] `.env` existe com `GEMINI_API_KEY` preenchida, e `git status` não o mostra.
- [x] `uv run python scripts/conferir_chave.py` diz que a chave é válida e o modelo está disponível.
- [x] A cota diária (RPD) do `gemini-3.8-flash` no projeto foi anotada.
- [x] `GEMINI_PLANO` está no `.env`. Se for `creditos-ai-pro`, o faturamento está em Prepay, com a recarga automática desligada e um teto mensal (spend cap).
- [x] `docker compose up --build` sobe a API (na primeira vez, baixa o modelo e constrói o índice nos volumes).
- [x] `POST /perguntar` em `http://localhost:8000/docs` responde a uma pergunta com resposta, páginas e Trechos.

## Comments

Resolvido em 09/11/2026. O autor rodou o wizard e fez todos os passos. Conferido pelo agente:
- `.env` ignorado pelo git;
- `conferir_chave.py` diz que a chave é válida e que o `gemini-3.8-flash` está disponível;
- `GEMINI_PLANO=gratuito` e `PROVEDOR=gemini`;
- Docker Desktop 29.9.3 com Compose v5.7.0;
- contêiner `rag-relatorio-sus-api-1` no ar, com o modelo de embeddings (2,1 GB) e o índice nos volumes;
- `GET /saude` responde 570 Trechos;
- o log do contêiner mostra um `POST /perguntar` do autor com 200 OK.

O autor declarou que anotou a cota diária (RPD); o agente não tem como conferir isso daqui.

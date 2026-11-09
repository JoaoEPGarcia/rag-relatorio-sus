# 06: Chave da API e Docker Desktop

**What to build:** o autor deixa a máquina pronta para as Rodadas e para subir a API em contêiner. Ele cria a chave do Gemini no Google AI Studio, na conta do Google AI Pro, e grava em `.env`. Se quiser os créditos mensais do AI Pro, vincula o plano ao Google Developer Program e liga o faturamento Prepay (mínimo de US$ 5, recarga automática desligada) no projeto da chave (ADR 0005); senão, fica no plano gratuito. Ele também anota a cota diária do `gemini-3.8-flash` que o AI Studio mostra (copiado de `.env.exemplo`, fora do git), e instala o Docker Desktop. É o passo 2.W do plano: o roteiro do wizard guia cada tela.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [ ] `.env` existe com `GEMINI_API_KEY` preenchida, e `git status` não o mostra.
- [ ] `uv run python scripts/conferir_chave.py` diz que a chave é válida e o modelo está disponível.
- [ ] A cota diária (RPD) do `gemini-3.8-flash` no projeto foi anotada.
- [ ] `GEMINI_PLANO` está no `.env`. Se for `creditos-ai-pro`, o faturamento está em Prepay, com a recarga automática desligada e um teto mensal (spend cap).
- [ ] `docker compose up --build` sobe a API (na primeira vez, baixa o modelo e constrói o índice nos volumes).
- [ ] `POST /perguntar` em `http://localhost:8000/docs` responde a uma pergunta com resposta, páginas e Trechos.

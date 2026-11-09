# 06: Chave da API e Docker Desktop

**What to build:** o autor deixa a máquina pronta para as Rodadas pagas e para subir a API em contêiner. Ele cria a chave da API da Anthropic e a grava em `.env` (copiado de `.env.exemplo`, fora do git), e instala o Docker Desktop. É o passo 2.W do plano: o roteiro do wizard guia cada tela.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [ ] `.env` existe com `ANTHROPIC_API_KEY` preenchida, e `git status` não o mostra.
- [ ] `docker compose up --build` sobe a API (na primeira vez, baixa o modelo e constrói o índice nos volumes).
- [ ] `POST /perguntar` em `http://localhost:8000/docs` responde a uma pergunta com resposta, páginas e Trechos.

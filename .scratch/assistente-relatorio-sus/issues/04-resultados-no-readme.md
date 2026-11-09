# 04: Resultados no README, em português e em inglês

**What to build:** quem chega ao repositório lê em "Principais resultados" afirmações com número, cada uma vinda do registro por marcador. São elas:

- o número de destaque, com IC, contra o acerto sem RAG;
- a comparação com o contexto completo, com custo e latência;
- a abstenção nas Perguntas sem resposta;
- a Classe de erro mais frequente.

Um achado nulo, se houver, é escrito com a mesma clareza. A seção "In English" traz os mesmos números com ponto decimal: o registro passa a guardar, para cada número, também o texto em inglês, e o README em inglês usa um marcador próprio para essa versão. A tabela do topo ganha os n reais (Perguntas, Tipos, sem resposta) por marcador.

**Blocked by:** 01 (Da Rodada aos números)

**Status:** ready-for-agent

- [ ] Teste: um número registrado gera o texto em pt-BR e em inglês ("80,0%" / "80.0%", "−5,0 p.p." / "−5.0 pp").
- [ ] O README gerado sobre a raiz sintética não tem marcador sem valor, e o conferidor de números passa.
- [ ] `README.base.md` não tem número digitado no texto corrido.
- [ ] O texto do README real só é regenerado com números reais no ticket 11.

# 04: Resultados no README, em português e em inglês

**What to build:** quem chega ao repositório lê em "Principais resultados" afirmações com número, cada uma vinda do registro por marcador. São elas:

- o número de destaque, com IC, contra o acerto sem RAG;
- a comparação com o contexto completo, com tokens de entrada e latência;
- a abstenção nas Perguntas sem resposta;
- a Classe de erro mais frequente.

Um achado nulo, se houver, é escrito com a mesma clareza. A seção "In English" traz os mesmos números com ponto decimal: o registro passa a guardar, para cada número, também o texto em inglês, e o README em inglês usa um marcador próprio para essa versão. A tabela do topo ganha os n reais (Perguntas, Tipos, sem resposta) por marcador.

**Blocked by:** 01 (Da Rodada aos números)

**Status:** resolved

- [x] Teste: um número registrado gera o texto em pt-BR e em inglês ("80,0%" / "80.0%", "−5,0 p.p." / "−5.0 pp").
- [x] O README gerado sobre a raiz sintética não tem marcador sem valor, e o conferidor de números passa.
- [x] `README.base.md` não tem número digitado no texto corrido.
- [x] O texto do README real só é regenerado com números reais no ticket 11.

## Comments

Resolvido na branch `integracao/assistente-relatorio-sus` (09/11/2026). O registro guarda `texto_en`; o README usa `{{chave:en}}` na seção "In English". As conclusões dependentes do sinal são textos registrados pela análise. O conferidor e o 06 carregam scripts e modelos de `config.PROJETO`, e os dados de `RAG_SUS_RAIZ`. O `README.md` real só é regenerado no ticket 11; até lá, o conferidor falha no checkout real por falta das chaves de resultado (esperado; o CI não roda o conferidor).

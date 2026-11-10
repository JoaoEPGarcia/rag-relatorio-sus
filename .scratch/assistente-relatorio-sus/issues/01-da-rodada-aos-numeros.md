# 01: Da Rodada aos números

**What to build:** quem roda a análise aponta para a pasta das Rodadas e para a folha de Revisão e recebe, no registro de números, todos os resultados publicáveis, mais as linhas das tabelas do Relatório de avaliação. O processamento:

- consolida a Rodada principal de cada Condição, exigindo a Revisão dos Veredictos do Juiz, e a Revisão do autor vence o Juiz;
- resume cada Condição com as três medidas e o intervalo de Wilson, separando as Perguntas respondíveis das sem resposta;
- compara com RAG × sem RAG (comparação principal) e com RAG × contexto completo: tabela 2×2, McNemar exato e Newcombe;
- cruza as Classes de erro com o Tipo de pergunta;
- calcula a concordância com cada repetição que existir;
- registra tokens, latência e fallbacks.

O número de destaque é o Acerto da resposta com RAG nas 50 respondíveis, com os limites do IC, contra o mesmo acerto sem RAG. É a seam de teste nova, aprovada na spec, escrita com TDD.

Inclui um gerador de Rodadas sintéticas de demonstração, que grava numa raiz temporária (variável de ambiente da raiz do projeto) e nunca no registro real. Os tickets 02, 03 e 05 o usam para verificação sem chamar o modelo.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Teste com Rodadas sintéticas: os números registrados por Condição (acerto, limites do IC, n) batem com uma conta feita à parte no teste.
- [x] O número de destaque usa só as Perguntas respondíveis, e as sem resposta saem em chaves próprias (abstenção correta com IC).
- [x] Faltando Revisão de algum Veredicto do Juiz na Rodada principal, a análise falha e lista as Perguntas pendentes.
- [x] A Revisão do autor prevalece sobre o Juiz, e o registro guarda quantos Veredictos foram revisados e quantos o autor mudou.
- [x] As linhas das tabelas LaTeX (resultados por Condição, comparação pareada, erros por Tipo de pergunta) saem em pt-BR, com `%` e o sinal de menos escapados, prontas para `\linhasde`.
- [x] Rodar a análise duas vezes não muda o registro (sem data, ordenado).
- [x] A concordância entre Rodadas só é registrada quando a repetição existe, e é rotulada como Veredictos não revisados.
- [x] O script de análise é uma casca fina sobre a função; o lint e todos os testes passam.

## Comments

Resolvido na branch `integracao/assistente-relatorio-sus` (09/11/2026). `rag_sus.avaliacao.resultados.analisar` (casca: `scripts/04_analisar.py`) grava o registro e as linhas de tabela em `relatorio/tabelas/`; o conferidor ignora essa pasta. Rodadas sintéticas: `scripts/gerar_rodadas_sinteticas.py` (só numa raiz temporária via `RAG_SUS_RAIZ`). Depois da revisão de código: vocabulário único em `avaliacao/vocabulario.py`, nível do IC tirado de `estatistica.NIVEL`, e a análise recusa Rodada principal sem `parametros` no `execucao.json`.

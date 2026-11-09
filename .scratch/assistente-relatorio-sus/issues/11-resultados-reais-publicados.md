# 11: Resultados reais publicados

**What to build:** o pipeline completo roda sobre as Rodadas reais e revisadas, e o repositório fica pronto para o autor torná-lo público. Isso gera:

- o registro de números;
- as figuras;
- as macros e as tabelas;
- o `NUMEROS_CANONICOS.md`;
- o README com os resultados em português e em inglês;
- o PDF do Relatório de avaliação, versionado.

As figuras são conferidas contra o `GUIA_ESTILO.md` e o checklist do chartosaur-viz, e as páginas do PDF são mostradas ao autor. A frase de currículo sai preenchida a partir do registro: "X% de acerto nas 50 respondíveis (IC 95%: a–b), contra Y% sem RAG".

**Blocked by:** 05 (Pipeline completo), 10 (Revisão dos Veredictos)

**Status:** ready-for-agent

- [ ] O pipeline completo roda do início ao fim sobre as Rodadas reais, com o conferidor "ok".
- [ ] Cada número do README, do PDF e das figuras está em `NUMEROS_CANONICOS.md` e sai de um script, e não há número sem origem.
- [ ] O PDF compila e foi mostrado ao autor, página a página.
- [ ] As figuras passam no `--validar` e no checklist do chartosaur-viz.
- [ ] A frase de currículo com X, a, b e Y reais foi entregue ao autor, tirada do registro.
- [ ] Commit feito; o repositório continua privado até o autor rodar o `gh repo edit ... --visibility public`.

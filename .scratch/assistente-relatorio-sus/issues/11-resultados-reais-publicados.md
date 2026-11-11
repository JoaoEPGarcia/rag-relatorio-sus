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

**Status:** resolved

- [x] O pipeline completo roda do início ao fim sobre as Rodadas reais, com o conferidor "ok".
- [x] Cada número do README, do PDF e das figuras está em `NUMEROS_CANONICOS.md` e sai de um script, e não há número sem origem.
- [x] O PDF compila e foi mostrado ao autor, página a página.
- [x] As figuras passam no `--validar` e no checklist do chartosaur-viz.
- [x] A frase de currículo com X, a, b e Y reais foi entregue ao autor, tirada do registro.
- [x] Commit feito; o repositório continua privado até o autor rodar o `gh repo edit ... --visibility public`.

## Comments

11/11/2026. O pipeline completo (`scripts/reproduzir.py`) rodou sobre a Rodada principal revisada e as duas repetições: análise, figuras, documentos, compilação, conferidor de números "ok" e conferência do Gabarito (60 de 60 revisadas, 0 problemas). As figuras passam no `--validar` do kit (as duas ressalvas são as do próprio kit, com a mitigação dele) e no checklist do chartosaur-viz. A leitura do PDF achou cinco problemas de texto e diagramação, corrigidos em `9b7c477`. A revisão de código (padrões e spec) foi corrigida em `ee25ff6`. A frase de currículo, tirada do registro: "78,0% de acerto nas 50 respondíveis (IC 95%: 64,8%–87,2%), contra 0,0% sem RAG". Resultados publicados em `790eab9`. O PDF foi aberto para o autor, página a página. Falta o autor: dar o de acordo no PDF e, quando quiser, tornar o repositório público com `gh repo edit JoaoEPGarcia/rag-relatorio-sus --visibility public`.

11/11/2026. O autor leu o PDF e aprovou ("perfeito, pode aprovar"). O repositório segue privado até o autor rodar `gh repo edit JoaoEPGarcia/rag-relatorio-sus --visibility public`.

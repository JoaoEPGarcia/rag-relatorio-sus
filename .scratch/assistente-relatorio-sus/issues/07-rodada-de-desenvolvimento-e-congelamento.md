# 07: Rodada de desenvolvimento e congelamento dos parâmetros

**What to build:** com o autor presente (há custo), roda-se a Rodada de desenvolvimento nas Perguntas de desenvolvimento, nas três Condições. O roteiro:

1. mostrar a contagem de chamadas antes de confirmar;
2. medir e mostrar o custo e a latência por Pergunta;
3. examinar os erros por Classe e ajustar, só com essas Perguntas, o número de Trechos, o tamanho do Trecho e os prompts, se necessário;
4. reconstruir os Trechos e o índice, se a quebra mudar;
5. congelar os parâmetros (`congelado = true`) por commit (ADR 0002).

Cada ajuste e o motivo dele ficam registrados (nota no `docs/DESENHO.md` ou ADR, se difícil de reverter). Os resultados de desenvolvimento ficam versionados, mas nunca entram no registro de números.

**Blocked by:** 06 (Chave da API e Docker Desktop)

**Status:** ready-for-human

- [ ] O autor aprovou o custo antes de cada execução com `--confirmar`.
- [ ] O custo medido por Pergunta e por Condição foi mostrado ao autor, com a estimativa da Rodada principal e das repetições.
- [ ] Os ajustes feitos (ou "nenhum") e o porquê estão registrados.
- [ ] `parametros.toml` está com `congelado = true` num commit, e a trava da Rodada principal libera.
- [ ] Nenhuma Pergunta do Gabarito foi usada para ajustar parâmetros.

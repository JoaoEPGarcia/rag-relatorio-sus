# 07: Rodada de desenvolvimento e congelamento dos parâmetros

**What to build:** com o autor presente (gasta cota do plano gratuito), roda-se a Rodada de desenvolvimento nas Perguntas de desenvolvimento, nas três Condições. O roteiro:

1. mostrar a contagem de chamadas antes de confirmar;
2. medir e mostrar os tokens e a latência por Pergunta, e quantos dias de cota a Rodada principal e as repetições vão levar;
3. examinar os erros por Classe e ajustar, só com essas Perguntas, o número de Trechos, o tamanho do Trecho e os prompts, se necessário;
4. reconstruir os Trechos e o índice, se a quebra mudar;
5. congelar os parâmetros (`congelado = true`) por commit (ADR 0002).

Cada ajuste e o motivo dele ficam registrados (nota no `docs/DESENHO.md` ou ADR, se difícil de reverter). Os resultados de desenvolvimento ficam versionados, mas nunca entram no registro de números.

**Blocked by:** 06 (Chave da API e Docker Desktop)

**Status:** ready-for-human

- [ ] O autor aprovou cada execução com `--confirmar`.
- [ ] Os tokens e a latência medidos por Pergunta e por Condição foram mostrados ao autor, com a estimativa de dias de cota da Rodada principal e das repetições.
- [ ] Se a cota diária do `gemini-3.8-flash` não comportar a avaliação em prazo razoável, o modelo foi trocado antes do congelamento, e a troca está no ADR 0005.
- [ ] Os ajustes feitos (ou "nenhum") e o porquê estão registrados.
- [ ] `parametros.toml` está com `congelado = true` num commit, e a trava da Rodada principal libera.
- [ ] Nenhuma Pergunta do Gabarito foi usada para ajustar parâmetros.

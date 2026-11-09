# 09: Rodada principal e repetições

**What to build:** com o autor presente (gasta cota do plano gratuito, talvez por mais de um dia), roda-se a Rodada principal nas 60 Perguntas e nas três Condições, com os parâmetros congelados e o Gabarito revisado (as travas verificam os dois). Ao fim, sai a folha de Revisão dos Veredictos do Juiz. Depois vêm as duas repetições, que só medem a concordância entre Rodadas. Cada execução registra o commit e os parâmetros ao lado das respostas, e as Rodadas ficam versionadas.

**Blocked by:** 07 (Rodada de desenvolvimento e congelamento), 08 (Revisão do Gabarito)

**Status:** ready-for-human

- [ ] O autor aprovou a contagem de chamadas antes de `--confirmar`.
- [ ] As três Condições têm as 60 linhas na Rodada principal, sem Pergunta faltando (a retomada cobre quedas e a cota diária esgotada).
- [ ] A folha de Revisão foi gerada com todos os Veredictos do Juiz da Rodada principal.
- [ ] As duas repetições estão completas.
- [ ] Respostas vindas de fallback do servidor, se houver, estão identificadas.

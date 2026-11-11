# 09: Rodada principal e repetições

**What to build:** com o autor presente (gasta cota do plano gratuito, talvez por mais de um dia), roda-se a Rodada principal nas 60 Perguntas e nas três Condições, com os parâmetros congelados e o Gabarito revisado (as travas verificam os dois). Ao fim, sai a folha de Revisão dos Veredictos do Juiz. Depois vêm as duas repetições, que só medem a concordância entre Rodadas. Cada execução registra o commit e os parâmetros ao lado das respostas, e as Rodadas ficam versionadas.

**Blocked by:** 07 (Rodada de desenvolvimento e congelamento), 08 (Revisão do Gabarito)

**Status:** resolved

- [x] O autor aprovou a contagem de chamadas antes de `--confirmar`.
- [x] As três Condições têm as 60 linhas na Rodada principal, sem Pergunta faltando (a retomada cobre quedas e a cota diária esgotada).
- [x] A folha de Revisão foi gerada com todos os Veredictos do Juiz da Rodada principal.
- [x] As duas repetições estão completas.
- [x] Respostas vindas de fallback do servidor, se houver, estão identificadas.

## Comments

10/11/2026. Rodada principal completa: 60 Perguntas × 3 Condições, com o `gemini-3.5-flash-lite` (commits `85d3e4c` e `fc1a063`, com os mesmos parâmetros congelados; só mudou o tratamento de tempo esgotado). Ela foi retomada três vezes: um Juiz preso, a memória baixa da máquina e a cota diária da cadeia do Juiz. A folha de Revisão saiu com 42 Veredictos do Juiz: com RAG, 15 certos e 6 errados; contexto completo, 20 certos e 1 errado. A folha em PDF (`scripts/gerar_folha_dos_veredictos.py`) foi aberta para o autor. A repetição 1 parou em 49 de 60 (com RAG), pela cota diária da cadeia do Juiz, e a repetição 2 não começou.

11/11/2026. Repetições completas. A repetição 1 terminou depois da renovação da cota do respondedor (contexto completo de 25 para 60), e a repetição 2 rodou inteira no mesmo dia, retomada algumas vezes por sobrecarga do servidor (HTTP 503), que não é cota. Cada execução agora guarda a lista de commits em que rodou (`execucao.json`, campo `commits`); a Rodada principal registra `85d3e4c`, `fc1a063` e `ad0ad19`, todos com os mesmos parâmetros congelados. Respostas vindas de fallback do servidor: o registro conta `principal_n_fallback` e as tabelas mostram a coluna; na Rodada principal, nenhuma. A contagem de chamadas foi aprovada pelo autor no chat antes de cada `--confirmar` ("pode gastar a cota"). Commits `81c883e` e `f896ca7`.

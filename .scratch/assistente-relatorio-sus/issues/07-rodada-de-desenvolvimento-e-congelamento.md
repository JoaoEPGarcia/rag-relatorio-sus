# 07: Rodada de desenvolvimento e congelamento dos parâmetros

**What to build:** com o autor presente (gasta cota do plano gratuito), roda-se a Rodada de desenvolvimento nas Perguntas de desenvolvimento, nas três Condições. O roteiro:

1. mostrar a contagem de chamadas antes de confirmar;
2. medir e mostrar os tokens e a latência por Pergunta, e quantos dias de cota a Rodada principal e as repetições vão levar;
3. examinar os erros por Classe e ajustar, só com essas Perguntas, o número de Trechos, o tamanho do Trecho e os prompts, se necessário;
4. reconstruir os Trechos e o índice, se a quebra mudar;
5. congelar os parâmetros (`congelado = true`) por commit (ADR 0002).

Cada ajuste e o motivo dele ficam registrados (nota no `docs/DESENHO.md` ou ADR, se difícil de reverter). Os resultados de desenvolvimento ficam versionados, mas nunca entram no registro de números.

**Blocked by:** 06 (Chave da API e Docker Desktop)

**Status:** resolved

- [x] O autor aprovou cada execução com `--confirmar`.
- [x] Os tokens e a latência medidos por Pergunta e por Condição foram mostrados ao autor, com a estimativa de dias de cota da Rodada principal e das repetições.
- [x] Se a cota diária do `gemini-3.8-flash` não comportar a avaliação em prazo razoável, o modelo foi trocado antes do congelamento, e a troca está no ADR 0005.
- [x] Os ajustes feitos (ou "nenhum") e o porquê estão registrados.
- [x] `parametros.toml` está com `congelado = true` num commit, e a trava da Rodada principal libera.
- [x] Nenhuma Pergunta do Gabarito foi usada para ajustar parâmetros.

## Comments

09/11/2026, primeira tentativa (autorizada pelo autor: "pode gastar a cota e fazer o 7").

- A Rodada de desenvolvimento parou na Condição com RAG depois de 5 das 12 Perguntas (D01 a D05): 5 chamadas ao respondedor e 2 ao Juiz. A API devolveu 429 com `quotaId` diário (`PerDay`), ou seja, a cota diária do `gemini-3.8-flash` acabou, contando também o uso anterior do dia (conferência da chave e o teste no Docker). Logo depois, a API parou de responder: duas chamadas de teste estouraram 60 s e 240 s.
- No que respondeu: 1.620 a 2.103 tokens de entrada e 293 a 805 de saída por Pergunta. D01 se absteve porque a recuperação não trouxe a p. 25. D02 e D04 acertaram pela regra, e D03 e D05 pelo Juiz, ainda sem Revisão.
- A latência registrada (131 a 249 s) não serve: `ProvedorGemini.gerar_json` mede o tempo em volta de `_post`, que inclui as esperas e as novas tentativas depois de 429 e 503. Antes da Rodada principal, a medida precisa cobrir só a requisição que deu certo.
- Com uma cota dessa ordem, a Rodada principal (180 chamadas ao respondedor, mais as do Juiz) e as duas repetições levariam semanas. O item "trocar o modelo antes do congelamento" passa a valer, e a decisão é do autor (ver a resposta no chat).
- As linhas gravadas ficam em `resultados/rodadas/desenvolvimento/` (sem commit). O mesmo comando retoma de D06.

10/11/2026, segunda tentativa, sem gastar dinheiro (o autor: "Vamos usar todos os modelos gratis pode prosseguir").

- Os modelos foram sondados e houve troca antes do congelamento (ADR 0005): o respondedor passou a ser o `gemini-3.5-flash-lite`, um modelo só, e o Juiz o `gemini-3.6-flash`, com os reservas em cadeia `gemini-3-flash-preview`, `gemini-3.1-flash-lite` e `gemini-3.8-flash`. As 5 linhas da primeira tentativa foram descartadas.
- A Rodada de desenvolvimento completou as 12 Perguntas nas três Condições, sem parada de cota. O Juiz julgou 9 vezes, todas com o `gemini-3.6-flash`.
- Mostrado ao autor (`resultados/rodadas/desenvolvimento/`):

  | Condição | acerto nas respondíveis | abstenção nas sem resposta | tokens de entrada (mediana) | latência (mediana) |
  |---|---|---|---|---|
  | com RAG | 8/10 | 2/2 | 1.621 | 3,1 s |
  | sem RAG | 0/10 (abstém-se) | 2/2 | 183 | 2,7 s |
  | contexto completo | 9/10 | 2/2 | 99.195 | 5,4 s |

- Com RAG, os dois erros (D01 e D07) são abstenções em Perguntas de tabela. O primeiro Trecho da página certa aparece nas posições 19 e 18 da busca, contra 1 ou 2 nas outras oito Perguntas. No contexto completo, o único erro foi D10, por falha de leitura.
- Ajustes: nenhum, fora a troca de modelo. O motivo está em `docs/DESENHO.md` (Avaliação, "Rodada de desenvolvimento").
- Cota: uma Rodada faz 180 chamadas ao respondedor, mais cerca de um quarto disso ao Juiz, na proporção da Rodada de desenvolvimento. A Rodada principal e as duas repetições somam 540 chamadas ao `gemini-3.5-flash-lite`. Neste dia, ele aceitou 39 chamadas sem bater na cota. O RPD exato aparece no AI Studio, e a Rodada é retomável de um dia para o outro.
- `parametros.toml` congelado (`congelado = true`) por commit.

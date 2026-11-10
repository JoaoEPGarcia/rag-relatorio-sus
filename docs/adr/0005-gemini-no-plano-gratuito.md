# O modelo é o Gemini, no plano gratuito ou com os créditos do Google AI Pro

O autor decidiu, em 09/11/2026, não pagar API de modelo além do Google AI Pro, que já assina. O respondedor e o Juiz passam a ser o Gemini 3.8 Flash (`gemini-3.8-flash`), chamado pela API REST do Google AI Studio. A API da Anthropic, prevista no desenho original, sai do projeto. O Ollama continua como provedor local, mas não gera números publicados.

## Por que o Gemini

A Condição contexto completo põe o Relatório-fonte inteiro no prompt (cerca de 360 mil caracteres, ou 60 mil palavras). Por isso, o modelo precisa de uma janela longa. O Gemini 3.8 Flash aceita 1.048.576 tokens de entrada, tem plano gratuito e faz saída estruturada por JSON Schema.

Descartados:

- **Groq**, porque relatos de 2026 dão cerca de 8 mil tokens por minuto no plano gratuito, o que não comporta o texto inteiro numa chamada.
- **Ollama**, porque um modelo que cabe nos 8 GB da RTX 5060 Ti não lê o relatório inteiro, e os resultados não seriam reproduzíveis por quem não tem a mesma GPU.

## Como o Google AI Pro entra

Segundo a documentação do AI Studio, os limites maiores do AI Pro valem só dentro da interface web do AI Studio (Playground e Build). O uso por chave de API é cobrado e gerido à parte. Para a API, o que o AI Pro dá são créditos mensais do Google Cloud, pelo Google Developer Program, e só para quem tem um projeto com Cloud Billing ativo. A documentação não diz o valor desses créditos.

São dois modos, escolhidos no wizard e gravados em `GEMINI_PLANO` no `.env`:

- **`gratuito`**: a chave fica no plano gratuito. Não há custo, mas a cota diária é menor. O Google pode usar os prompts para melhorar os produtos dele. Os prompts levam só o Relatório-fonte, cuja publicação é autorizada, e Perguntas sobre ele, sem dado pessoal.
- **`creditos-ai-pro`**: o AI Pro é vinculado ao Google Developer Program, e o projeto da chave passa a ter faturamento **Prepay**. O Google pede um pré-pagamento mínimo de US$ 5, e os créditos do Cloud são gastos antes desse saldo. O projeto vai para o Tier 1, com cota maior, e os prompts deixam de ser usados para melhorar os produtos do Google. A recarga automática fica desligada, e é isso que limita o gasto: quando o saldo zera, a API devolve 402, e `03_rodar_avaliacao.py` para. O Postpay fica proibido, porque cobra no fim do mês sem esse teto. A documentação avisa que o corte pode atrasar uns 10 minutos, então o saldo pode ficar um pouco negativo. Por isso também se define um teto mensal (spend cap) na página Spend do projeto.

Preços do Tier pago em 09/11/2026, por milhão de tokens, para o `gemini-3.8-flash`: US$ 0,75 a entrada, US$ 3,75 a saída (inclusive o raciocínio) e US$ 0,075 a entrada lida do cache, até 31/12/2026. A partir de 01/01/2027, os três dobram. A Rodada de desenvolvimento mede os tokens por Pergunta, e é com eles que se estima o gasto das Rodadas seguintes antes de confirmar.

## Consequências

- **Cota e saldo.** A cota vale por projeto e por modelo e renova à meia-noite do Pacífico. Uma Rodada principal faz cerca de 180 chamadas ao respondedor, mais as do Juiz. Quando a cota diária acaba ou o saldo zera, `03_rodar_avaliacao.py` para e avisa. A Rodada é retomável, e o mesmo comando continua de onde parou.
- **Custo medido em tokens.** Não há estimativa em dólar por Pergunta. A comparação "se cabe no contexto, para que RAG?" usa os tokens de entrada e a latência por Pergunta.
- **O mesmo modelo nos dois modos.** O modo muda só a cota e quem paga. O modelo e os parâmetros são os mesmos, então os números não dependem do modo.
- **Sem fallback do servidor.** O registro guarda o `modelVersion` que respondeu, e `usou_fallback` só fica verdadeiro se ele diferir do modelo pedido.
- **Troca de modelo.** Se a cota do 3.8 Flash for pequena demais, a troca do modelo em `parametros.toml` (por exemplo, por um Flash-Lite) é feita antes do congelamento (ADR 0002) e fica registrada aqui.

## Troca de modelo antes do congelamento (10/11/2026)

Na Rodada de desenvolvimento, a cota diária do `gemini-3.8-flash` no plano gratuito acabou depois de 5 Perguntas, e o modelo depois parou de responder. O autor não quer gastar dinheiro, e os créditos do AI Pro exigem o pré-pagamento mínimo de US$ 5. Por isso, a avaliação fica no plano gratuito, somando a cota de vários modelos. A cota é por modelo. Os modelos foram sondados com uma chamada curta cada:

- respondem: `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite` e `gemini-3-flash-preview`;
- não servem: `gemini-3.5-flash`, que é outro nome do 3.6 (a API responde como `gemini-3.6-flash`); os Pro e o `gemini-4-argon`, que no plano gratuito recusam por todos os limites ao mesmo tempo; e o `gemini-2.5-flash-lite`, que não é mais oferecido a usuários novos.

A decisão:

- **Respondedor: `gemini-3.5-flash-lite`, um modelo só, em todas as Condições e Rodadas.** Trocar o respondedor no meio misturaria dois sistemas na comparação entre Condições. O Flash-Lite é o tipo de modelo com a maior cota no plano gratuito, e o objetivo do projeto é comparar as Condições com o mesmo modelo, e não o modelo mais forte.
- **Juiz: `gemini-3.6-flash`, seguido dos reservas `gemini-3-flash-preview`, `gemini-3.1-flash-lite` e `gemini-3.8-flash` (`reservas` em `parametros.toml`).** Quando a cota diária de um acaba, o seguinte assume (`ProvedorEmCadeia`). O Juiz pode trocar porque todo Veredicto dele na Rodada principal passa pela Revisão do autor, que vence o Juiz. Cada linha da Rodada grava o modelo que julgou (`modelo_juiz`), e o registro de números publica os modelos que de fato julgaram.
- O modelo do respondedor fica fora da cadeia do Juiz, para que a cota dele sirva só às respostas.
- As 5 linhas da primeira tentativa (respondidas pelo `gemini-3.8-flash`) foram descartadas, e a Rodada de desenvolvimento recomeça com o modelo novo.

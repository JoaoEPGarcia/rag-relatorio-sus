# Assistente do relatório Gestão Hospitalar no SUS-SP

Um assistente que responde perguntas sobre um relatório de pesquisa, citando a página, e a avaliação estatística que mede quanto ele acerta.

## Documentos

**Relatório-fonte**:
O relatório "Gestão Hospitalar no SUS-SP", em PDF, sobre o qual o assistente responde.
_Evite_: documento, PDF, relatório (sem qualificação)

**Relatório de avaliação**:
O relatório técnico produzido por este projeto, que descreve o assistente e os resultados da avaliação.
_Evite_: relatório (sem qualificação), paper

**Trecho**:
Pedaço contíguo do texto do Relatório-fonte, sempre dentro de uma única página, que o assistente pode recuperar e usar como base para responder. Uma tabela ou uma legenda de figura forma um Trecho próprio.
_Evite_: chunk, fragmento, passagem

**Página**:
A página impressa no rodapé do Relatório-fonte, que é a que se cita. A posição no arquivo (**página do PDF**) é a impressa mais um, porque a capa não tem número.
_Evite_: folha, página (sem qualificação, quando houver dúvida entre as duas)

## Avaliação

**Pergunta**:
Uma questão sobre o Relatório-fonte, feita em linguagem natural, usada para avaliar o assistente.
_Evite_: query, consulta

**Pergunta respondível**:
Pergunta cuja resposta está no texto do Relatório-fonte, inclusive em tabela ou legenda. Uma resposta que só existe dentro da imagem de um gráfico não conta.

**Tipo de pergunta**:
Onde está a resposta de uma Pergunta respondível: **número na prosa**, **número em tabela**, **número em legenda**, **conceito ou método**, ou **síntese entre páginas**.

**Pergunta de desenvolvimento**:
Pergunta usada só para construir e ajustar o assistente. Nunca entra no Gabarito nem nos resultados publicados.
_Evite_: pergunta de treino, pergunta de teste

**Pergunta sem resposta**:
Pergunta cuja resposta não está no Relatório-fonte; nela, o comportamento certo é a Abstenção.
_Evite_: pergunta impossível, pergunta capciosa

**Abstenção**:
Resposta em que o assistente declara que o Relatório-fonte não trata do que foi perguntado, em vez de responder.
_Evite_: recusa

**Gabarito**:
A resposta certa de uma Pergunta e a(s) página(s) do Relatório-fonte que a sustentam. Só vale depois da Revisão.
_Evite_: ground truth, resposta esperada

**Revisão**:
A conferência de um Gabarito, feita pelo autor do projeto diretamente no Relatório-fonte. Nenhum Gabarito entra na avaliação sem ela.

**Condição**:
A forma como o assistente responde numa rodada de avaliação: **com RAG** (recebe os Trechos recuperados), **sem RAG** (responde só com o que o modelo já sabe) ou **contexto completo** (recebe o texto inteiro do Relatório-fonte).
_Evite_: cenário, braço, variante

**Rodada**:
Uma passagem de todas as Perguntas do Gabarito por uma Condição. A **rodada principal** é a única cujos Veredictos passam pela Revisão e viram o resultado publicado; as **repetições** servem só para medir quanto os Veredictos mudam de uma Rodada para outra.

**Classe de erro**:
O motivo de uma resposta errada: **falha de recuperação**, **falha de leitura**, **abstenção indevida**, **resposta inventada** ou **citação errada**.

**Veredicto**:
A decisão, para uma Pergunta numa Condição, de que a resposta acertou ou errou.

**Juiz**:
Quem emite o Veredicto de uma resposta descritiva: um modelo de linguagem, cujos Veredictos passam pela Revisão antes de valer como resultado.

**Acerto da resposta**:
O conteúdo da resposta coincide com o Gabarito. É a medida principal.

**Acerto da citação**:
A página citada pelo assistente está entre as páginas do Gabarito.

**Acerto da recuperação**:
Alguma página do Gabarito está entre as páginas dos Trechos recuperados. Só existe na Condição com RAG.

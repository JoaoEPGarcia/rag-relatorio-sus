# Spec: Assistente do relatório Gestão Hospitalar no SUS-SP, avaliado com estatística

Status: ready-for-agent

Vocabulário: `GLOSSARY.md`. Decisões difíceis de reverter: `docs/adr/` (0001 FAISS com busca exata; 0002 parâmetros congelados antes da Rodada principal; 0003 README gerado por script; 0004 página impressa na citação). Registro completo da entrevista de desenho: `docs/DESENHO.md`.

## Problem Statement

O autor, estatístico que busca vagas de dados e ML (VTEX, iFood, Sezzle, Artefact), não tem no portfólio nenhum projeto com LLM, RAG, API ou Docker. Essa é a lacuna mais frequente nas vagas que ele mira: LLM, IA generativa e RAG aparecem em 12 de 43 vagas, e engenharia de software com APIs e Docker, em 10. Ao mesmo tempo, quase todo projeto de RAG que um recrutador vê é uma demonstração sem medida: o assistente "parece responder bem", mas ninguém sabe com que frequência acerta, nem se o acerto vem da busca no documento ou do que o modelo já sabia. O diferencial do autor é a estatística, e o projeto precisa mostrá-la.

Há também um problema de confiança no próprio número. Uma taxa de acerto calculada sobre um gabarito que ninguém conferiu, ou com parâmetros ajustados olhando a prova, ou com números digitados à mão no README, não vale nada numa entrevista. O autor quer que cada número publicado possa ser refeito por script e defendido.

## Solution

Um assistente que responde perguntas em português sobre o Relatório-fonte ("Gestão Hospitalar no SUS-SP", PDF de 175 páginas, com publicação autorizada) e cita a Página impressa de onde tirou a resposta. Ele é exposto por uma API FastAPI empacotada em Docker. Junto vem uma avaliação estatística, entregue num Relatório de avaliação em LaTeX e resumida no README:

- 60 Perguntas, propostas a partir do texto e conferidas pelo autor no PDF: 50 respondíveis, em cinco Tipos de pergunta com 10 de cada, e 10 sem resposta no relatório;
- três Condições sobre as mesmas Perguntas: com RAG, sem RAG e contexto completo;
- três medidas (Acerto da resposta, da citação e da recuperação), cada uma com intervalo de Wilson de 95%;
- comparação pareada entre Condições (McNemar exato e intervalo de Newcombe);
- Classes de erro cruzadas com o Tipo de pergunta, e custo e latência por Pergunta.

As regras de confiança viram código:

- a avaliação recusa um Gabarito com qualquer linha sem Revisão;
- a Rodada principal recusa parâmetros não congelados por commit;
- todo Veredicto do Juiz passa pela Revisão do autor;
- todo número impresso sai de um registro alimentado por script, e um conferidor falha diante de número digitado.

O número de destaque (README e frase de currículo) é o Acerto da resposta nas 50 Perguntas respondíveis, com IC de 95%, contra o mesmo acerto sem RAG.

**Estado atual.** Já estão implementados e testados (163 testes):

- a extração e a quebra em Trechos (570 Trechos);
- o índice de busca exata;
- as três Condições do assistente e os provedores Gemini (plano gratuito) e Ollama;
- o Juiz;
- a execução retomável de uma Rodada, a folha de Revisão dos Veredictos e a consolidação;
- a estatística e a análise;
- as travas;
- a geração do README, das macros LaTeX e de `NUMEROS_CANONICOS.md`, e o conferidor de números;
- a API, o Dockerfile, o docker-compose e o CI.

A proposta do Gabarito e as Perguntas de desenvolvimento estão escritas e aguardam a Revisão do autor.

Falta:

- a análise final que transforma as Rodadas em números registrados e tabelas;
- as figuras;
- o Relatório de avaliação em LaTeX;
- o script que roda o pipeline inteiro;
- os resultados no README;
- a Rodada de desenvolvimento, o ajuste e o congelamento dos parâmetros;
- a Rodada principal, a Revisão dos Veredictos e as repetições.

## User Stories

### Quem usa o assistente

1. Como gestor de saúde, quero perguntar em português sobre o Relatório-fonte e receber uma resposta curta, para não precisar ler 175 páginas atrás de um número.
2. Como gestor, quero que cada resposta cite a Página impressa no rodapé, para conferir no PDF em segundos.
3. Como gestor, quero ver os Trechos em que a resposta se apoiou, para julgar se ela está bem fundamentada.
4. Como gestor, quero que o assistente diga que o relatório não trata do assunto quando for o caso, em vez de inventar, para não tomar decisão com base num número que não existe.
5. Como gestor, quero que os números venham no formato brasileiro e exatamente como no relatório, sem arredondar, para poder citá-los sem reconferir a grafia.
6. Como gestor, quero respostas sobre números que estão em tabelas e em legendas de figura, e não só no texto corrido, porque é nas tabelas que o relatório guarda os detalhes por rede.
7. Como desenvolvedor que integra o assistente, quero um endpoint `POST /perguntar` com contrato documentado no Swagger, para chamá-lo de outro sistema.
8. Como desenvolvedor, quero um endpoint de saúde que diga quantos Trechos estão indexados, para saber se o serviço subiu com o índice certo.
9. Como desenvolvedor, quero subir a API com um único `docker compose up`, para não montar ambiente Python à mão.
10. Como desenvolvedor, quero que a imagem Docker não carregue o modelo de embeddings de 2,24 GB, e que ele seja baixado uma vez para um volume, para que a imagem seja leve e o modelo não seja baixado a cada build.
11. Como desenvolvedor, quero que uma falha do modelo vire um erro 502 sem detalhes internos, para que a API nunca vaze credenciais ou mensagens do provedor.
12. Como pessoa que não quer pagar API além do Google AI Pro que já assina, quero que o projeto rode no plano gratuito do Gemini ou com os créditos mensais do AI Pro, com o gasto limitado ao saldo pré-pago, e que eu possa trocar para um modelo local via Ollama por uma variável do `.env`, sabendo que os números publicados não vêm do Ollama (ADR 0005).

### Quem avalia o projeto (recrutador, entrevistador técnico)

13. Como recrutador, quero ler no topo do README a pergunta do projeto e os principais resultados com número e intervalo, para entender o valor do projeto em um minuto.
14. Como entrevistador técnico, quero ver a taxa de acerto com IC de 95%, e não um número solto, para saber quanta incerteza há com 50 Perguntas.
15. Como entrevistador, quero ver a comparação com RAG contra sem RAG, pareada e com teste adequado, para saber quanto do acerto vem da busca no documento.
16. Como entrevistador, quero ver uma terceira Condição com o relatório inteiro no contexto, junto com o custo e a latência por Pergunta, para responder à pergunta "se cabe no contexto, para que RAG?".
17. Como entrevistador, quero ver os erros classificados (falha de recuperação, falha de leitura, abstenção indevida, resposta inventada, citação errada) e cruzados com o Tipo de pergunta, para saber onde o sistema falha.
18. Como entrevistador, quero ver o Acerto da recuperação separado do Acerto da resposta, para distinguir problema de busca de problema de leitura.
19. Como entrevistador, quero saber que os parâmetros foram congelados antes da Rodada principal, e não ajustados olhando a prova, para confiar que a taxa não está inflada.
20. Como entrevistador, quero saber que o Gabarito foi conferido por uma pessoa no PDF e que os Veredictos do Juiz foram revisados, para confiar no que conta como acerto.
21. Como entrevistador, quero ver quanto os Veredictos mudam de uma Rodada para outra, para saber se o resultado depende do sorteio do modelo.
22. Como entrevistador, quero ver as limitações declaradas (só texto, amostra pequena, um documento, Gabarito proposto com ajuda de um modelo), para julgar o que os dados não autorizam afirmar.
23. Como entrevistador, quero ler um Relatório de avaliação curto, de 10 a 15 páginas, com o mesmo visual dos outros projetos do portfólio, para avaliar a comunicação técnica do autor.
24. Como entrevistador, quero que cada figura afirme o achado no título, com uma cor de destaque e a fonte no rodapé, para ler o resultado sem decifrar o gráfico.
25. Como entrevistador, quero clonar o repositório e refazer a análise a partir das Rodadas versionadas sem pagar a API, para conferir os números.
26. Como entrevistador, quero ver testes automatizados e CI passando, para avaliar a disciplina de engenharia.
27. Como entrevistador, quero ver ADRs que expliquem as decisões menos óbvias (FAISS em vez de Chroma, página impressa, README gerado), para entender o raciocínio, e não só o código.

### O autor

28. Como autor, quero que o script de avaliação recuse um Gabarito com qualquer linha sem Revisão, para que um gabarito não conferido nunca vire resultado.
29. Como autor, quero que cada linha proposta do Gabarito traga o trecho de apoio, os pontos de atenção da extração e as outras páginas onde a mesma resposta parece estar, para revisar rápido e listar todas as páginas válidas.
30. Como autor, quero uma conferência mecânica do Gabarito contra o texto extraído (formato, páginas, valores presentes na página), para pegar erro grosseiro antes de abrir o PDF.
31. Como autor, quero ajustar o número de Trechos, o tamanho do Trecho e os prompts só com Perguntas de desenvolvimento, para não contaminar a prova.
32. Como autor, quero que a Rodada principal se recuse a rodar enquanto os parâmetros não estiverem congelados e commitados, para que o congelamento fique no histórico.
33. Como autor, quero ver quantas chamadas uma Rodada fará antes de gastar a cota do plano gratuito, só chamar o modelo com uma confirmação explícita e, se a cota diária acabar, continuar no dia seguinte de onde parou.
34. Como autor, quero que uma Rodada interrompida continue de onde parou, para não pagar de novo por respostas já obtidas.
35. Como autor, quero que respostas numéricas certas sejam pontuadas por regra, sem Juiz, para gastar menos e não depender de modelo no caso fácil.
36. Como autor, quero que respostas numéricas reprovadas pela regra também passem pelo Juiz e pela minha Revisão, para que um falso negativo da regra (como "−0,62" contra "0,62 para baixo") não vire erro injusto.
37. Como autor, quero uma folha CSV com os Veredictos do Juiz, onde preencho "certo" ou "errado", preservada quando o script roda de novo, para revisar no Excel sem perder o trabalho.
38. Como autor, quero que a análise final se recuse a publicar enquanto houver Veredicto do Juiz sem Revisão, e que a minha Revisão vença o Juiz, para que o número publicado seja o que eu conferi.
39. Como autor, quero que cada resposta registre o modelo que de fato respondeu e se houve fallback do servidor, para declarar no relatório se algum modelo diferente respondeu.
40. Como autor, quero que todo número impresso (README, Relatório de avaliação, títulos e rótulos de figura) saia de um registro único alimentado pelos scripts, para nunca digitar número.
41. Como autor, quero que o README seja gerado de um modelo com marcadores, e que um conferidor falhe se alguém editar o README à mão ou digitar número no `.tex`, para que a regra dos números não dependa de memória.
42. Como autor, quero o `NUMEROS_CANONICOS.md` gerado com as colunas do kit (número, valor, o que é, de que script sai, onde aparece), para saber o que conferir quando um número mudar.
43. Como autor, quero rodar o pipeline inteiro com um comando que pare no primeiro erro, para refazer tudo depois de uma mudança.
44. Como autor, quero que as credenciais fiquem só no `.env`, fora do git, com um `.env.exemplo` versionado, para publicar o repositório sem risco.
45. Como autor, quero tirar do Relatório de avaliação a frase de currículo com os números reais (acerto com IC contra o acerto sem RAG), para levar o projeto ao currículo e ao LinkedIn.
46. Como autor, quero que o repositório fique privado até a entrega e que eu mesmo o torne público, para controlar o que vai para o ar.

## Implementation Decisions

### Já implementado (não refazer; estender se preciso)

- **Extração**: lê o PDF página a página com pdfplumber.
  - Tolerância horizontal de 1,5 pt, porque o texto justificado cola as palavras com a tolerância padrão.
  - Normalização NFKC e desfazimento da hifenização de fim de linha.
  - Classifica cada linha pelo layout do LaTeX do Relatório-fonte:
    - corpo em 10,9 pt, com parágrafo novo pelo recuo;
    - títulos em negrito, 14,3 pt (capítulo) e 12,0 pt (seção);
    - legendas em 10,0 pt, começando por "Figura N:" ou "Tabela N:";
    - rótulos de painel e linhas só de símbolos são descartados.
  - O título da seção em vigor atravessa as páginas.
  - Tabelas:
    - os fragmentos que o pdfplumber separa nos filetes são juntados;
    - a serialização é linha a linha, cada célula com o nome da sua coluna, e trata cabeçalho em dois níveis, linha de grupo e rótulo herdado;
    - a legenda da tabela vira a primeira linha dela;
    - uma tabela que continua na página seguinte herda a legenda, marcada como continuação.
  - A capa fica fora. A Página impressa é a página do PDF menos um (ADR 0004).
- **Quebra**:
  - nenhum Trecho atravessa a página;
  - um parágrafo que cabe no alvo vai inteiro para o Trecho;
  - um parágrafo grande é dividido por frase, e uma frase gigante, por palavra;
  - a sobreposição é de frases inteiras, só dentro da página e da mesma seção;
  - o título da seção abre cada Trecho;
  - tabela e legenda são Trechos próprios, e uma tabela longa é dividida por linha, repetindo a legenda;
  - os identificadores são estáveis e derivados da Página.
- **Busca** (ADR 0001):
  - `multilingual-e5-large` via fastembed (ONNX, sem PyTorch), com os prefixos "query: " e "passage: " postos pelo projeto;
  - FAISS `IndexFlatIP` sobre vetores normalizados, ou seja, cosseno exato;
  - persistência em bytes, porque o FAISS falha com caminho não ASCII no Windows;
  - a carga recusa índice construído com outro modelo.
- **Assistente**: o mesmo esquema de saída nas três Condições, com resposta, páginas citadas e flag de abstenção.
  - Com RAG: os k Trechos marcados com "[página N | tipo]" vão na mensagem.
  - Sem RAG: nada do relatório vai ao modelo.
  - Contexto completo: o texto inteiro, página por página, vai no prompt de sistema, com cache de prompt.
  - Os prompts não mencionam nenhum fato do Relatório-fonte, porque isso vazaria a resposta na Condição sem RAG.
- **Provedores**: interface única que recebe sistema, mensagem e esquema JSON e devolve dados e metadados.
  - Gemini (ADR 0005):
    - Gemini 3.8 Flash no plano gratuito, pela API REST, com nível de raciocínio explícito e saída estruturada por `responseJsonSchema`;
    - o bloqueio de segurança vira exceção, e `maxOutputTokens` estourado vira erro;
    - o erro 429 de cota por minuto espera o tempo indicado pela API e tenta de novo; o de cota diária vira `CotaDiariaEsgotada`, e o 402 de saldo pré-pago zerado vira `SaldoEsgotado`.
  - Metadados: modelo que respondeu, tokens (inclusive os lidos do cache implícito), latência e id da requisição. O custo em dólar é zero, e o custo de cada Condição é medido em tokens de entrada.
  - Ollama: alternativa sem números publicados.
  - A escolha do provedor é feita pelo `.env`.
- **Juiz**: compara a resposta com o Gabarito pelo conteúdo, com os mesmos números quando houver, e ignora as páginas. Saída estruturada com Veredicto e justificativa curta. Abstenção conta como erro.
- **Gabarito**:
  - CSV com id, pergunta, tipo, resposta, valores, páginas, revisado e observação;
  - validação: tipo válido, respondível com página, sem resposta sem página, numérico com valores, síntese com pelo menos duas páginas, id único;
  - a trava da Revisão recusa o arquivo inteiro e lista as linhas pendentes.
- **Pontuação**:
  - números extraídos no formato brasileiro, com sinal só depois de espaço ou parêntese;
  - acerto numérico exige que todos os valores apareçam exatamente na resposta;
  - acerto da citação e da recuperação por interseção de páginas;
  - Classes de erro mutuamente exclusivas, derivadas das medidas, sem falha de recuperação nas Condições que não recuperam.
- **Rodada**:
  - grava uma linha JSONL por Pergunta e é retomável;
  - Juiz só quando necessário;
  - folha de Revisão que preserva o já revisado;
  - consolidação: Revisão do autor, senão Juiz, senão regra, com recusa quando falta Revisão.
- **Análise**:
  - resumo por Condição: medidas com Wilson, respondíveis e sem resposta em separado, custo médio, latência mediana e fallbacks;
  - comparação pareada por id nas respondíveis (tabela 2×2, McNemar exato, Newcombe método 10);
  - erros por Tipo de pergunta;
  - concordância entre Rodadas pelo Veredicto automático.
- **Travas**: a Rodada principal e as repetições exigem `congelado = true` em `parametros.toml` e o arquivo commitado.
- **Números e documentos** (ADR 0003):
  - registro único JSON, ordenado e sem data, com o texto já formatado em pt-BR (inteiro, ano, decN, pct1, pp1, p3, usd2);
  - chaves viram macros `\NumXxx`, com dígitos por extenso;
  - o README é gerado do modelo com marcadores `{{chave}}`;
  - o `NUMEROS_CANONICOS.md` sai nas colunas do kit;
  - conferidores de dígitos digitados no Markdown (fora de código, links, marcadores e listas) e no `.tex` (fora de comandos, opções e comentários).
- **API**:
  - FastAPI, com `POST /perguntar` (validação de 3 a 1000 caracteres) e `GET /saude`;
  - o assistente é montado na subida e injetável para testes;
  - o erro do modelo vira 502 sem detalhe interno.
- **Docker e CI**:
  - imagem com o código e os Trechos;
  - modelo de embeddings e índice em volumes nomeados, criados na primeira subida;
  - o CI roda ruff, pytest sem os testes lentos e o build da imagem.
- **Parâmetros atuais** (rascunho, não congelados): alvo de 180 palavras, sobreposição de 30, k de 6; respondedor e Juiz em Gemini 3.8 Flash com raciocínio `medium`; 2 repetições.

### A implementar

- **Do resultado aos números** (seam nova, aprovada):
  - Um módulo de resultados, com uma função que recebe a pasta das Rodadas e a folha de Revisão.
  - Consolida a Rodada principal de cada Condição e exige a Revisão.
  - Resume cada Condição e compara com RAG × sem RAG (a comparação principal) e com RAG × contexto completo.
  - Cruza erros por Tipo de pergunta e calcula a concordância com cada repetição que existir.
  - Grava cada número no registro, com chave estável e formato pt-BR, e escreve as linhas das tabelas LaTeX (que o kit lê com `\linhasde`).
  - Registra também:
    - o número de destaque: Acerto da resposta com RAG nas 50 respondíveis, com os limites do IC, e o mesmo acerto sem RAG;
    - os n de cada grupo, o número de Veredictos revisados e quantos o autor mudou em relação ao Juiz;
    - os fallbacks e os tokens totais.
  - O script de análise é uma casca fina sobre essa função.
- **Figuras** (kit `estilo_portfolio.py`, regras do `GUIA_ESTILO.md` e checklist da skill chartosaur-viz):
  - Acerto da resposta por Condição, com o IC de Wilson: com RAG em destaque e as demais em neutro.
  - Classes de erro por Tipo de pergunta na Condição com RAG.
  - Tokens de entrada e latência por Pergunta contra o acerto, por Condição.
  - Cada título afirma o achado com número tirado do registro por f-string, com a fonte no rodapé.
  - O script registra os números que imprime, declarando onde aparecem.
  - O validador do kit precisa passar.
- **Relatório de avaliação**:
  - cópia de `modelo_relatorio.tex`, sem editar o preâmbulo do kit;
  - capa com os dados do autor (João Eduardo Pastori Garcia, LinkedIn `joao-eduardo-garcia`, GitHub `JoaoEPGarcia`);
  - seções: problema, pipeline, desenho da avaliação (Gabarito, Revisão, Condições, medidas, pré-registro), resultados com intervalos, comparação pareada, erros por tipo, tokens e latência, variabilidade entre Rodadas, limitações;
  - uma caixa de destaque por seção, no máximo;
  - todos os números por macro;
  - compilação com pdfLaTeX, PDF versionado.
- **Pipeline completo**: um script que roda os passos na ordem e para no primeiro erro, com stdout em UTF-8 no Windows. A Rodada paga não é executada por padrão; ele refaz a partir das Rodadas versionadas.
  - extração e indexação, só quando faltam;
  - análise;
  - figuras;
  - documentos;
  - compilação do relatório;
  - conferidor de números;
  - conferência mecânica do Gabarito.
- **README**: a seção "Principais resultados" passa a usar marcadores do registro, com cada resultado escrito como afirmação com número, inclusive o achado nulo, se houver. A seção "In English" ganha os mesmos números com ponto decimal, também por marcador. Isso exige formato em inglês no registro, ou um segundo texto por chave.
- **Operação das Rodadas** (passos que dependem do autor, nesta ordem):
  1. o autor grava a chave gratuita do Gemini no `.env`;
  2. Rodada de desenvolvimento com as Perguntas de desenvolvimento, mostrando os tokens e a latência medidos e quantas chamadas cabem na cota diária;
  3. ajuste dos parâmetros só com elas, e congelamento por commit;
  4. o autor revisa o Gabarito;
  5. Rodada principal nas três Condições;
  6. o autor revisa os Veredictos na folha;
  7. as duas repetições;
  8. análise, figuras, relatório e README.
  - As Rodadas ficam versionadas, com o commit e os parâmetros de cada execução registrados ao lado.

## Testing Decisions

- **O que é um bom teste aqui**: ele exercita o comportamento externo pela interface pública do módulo, com entradas pequenas e legíveis, e falha por um motivo que se explica em uma frase. Ele não depende de detalhes internos (nomes de funções privadas, ordem de chamadas), nem de rede, nem da API do modelo, nem do modelo de 2,24 GB. Os dados de teste parecem os reais: frases que começam com maiúscula e tabelas com a forma das do Relatório-fonte.
- **Seam nova aprovada: "da Rodada aos números"**. Testada com Rodadas sintéticas (JSONL) e folha de Revisão gravadas numa pasta temporária, nunca em `resultados/`. Os testes verificam:
  - os números registrados para cada Condição: acerto, limites do IC e n;
  - a comparação pareada;
  - a recusa quando falta Revisão;
  - a prevalência da Revisão sobre o Juiz;
  - que o número de destaque usa só as 50 respondíveis;
  - que as linhas das tabelas LaTeX saem no formato pt-BR e escapadas;
  - que rodar duas vezes não muda o registro.
- **Seams existentes, mantidas**:
  - `Assistente.responder` com provedor falso, que cobre os prompts e as Condições;
  - geração de documentos e conferidor;
  - unidades de quebra, busca (com embutidor falso por saco de palavras), estatística, Gabarito, pontuação, extração, travas, Rodada, análise e API.
- **Arte anterior no código**:
  - o statsmodels serve de oráculo independente para Wilson e McNemar;
  - o intervalo de Newcombe é conferido por propriedades (contém a estimativa, espelha ao trocar as Condições, encolhe com mais pares) e por uma conta refeita passo a passo;
  - o embutidor falso e o provedor falso são reutilizados entre os arquivos de teste;
  - os testes `lento`, que leem o PDF inteiro, ficam fora do CI.
- **Sem teste de unidade, com outra verificação**:
  - as figuras, pelo validador do kit, pelo checklist chartosaur-viz e pelos números registrados pelo script;
  - o LaTeX, pela compilação e pelo conferidor de números;
  - a API do Gemini de verdade, pela conferência da chave (que não gasta cota) e pela Rodada de desenvolvimento.
- **TDD**: os módulos de quebra, busca e avaliação (inclusive a seam nova) são escritos com o teste antes do código.

## Out of Scope

- Ler os valores que só existem dentro das imagens de gráfico (visão computacional ou OCR). As Perguntas que dependem deles ficam fora do Gabarito, e isso é declarado nas limitações.
- Busca híbrida (vetorial + BM25), reranqueamento e ajuste fino de modelo: possíveis extensões, não nesta versão.
- Interface web e deploy público da API.
- Números publicados a partir do Ollama ou de outro provedor que não o Gemini.
- Gasto além dos créditos do Google AI Pro: o faturamento, se ligado, é Prepay sem recarga automática (ADR 0005).
- Outros documentos além do Relatório-fonte.
- Um "acerto geral" sobre as 60 Perguntas como número de destaque.
- Tornar o repositório público, que é feito pelo autor no passo de publicação.

## Further Notes

- **Publicação**: o repositório `JoaoEPGarcia/rag-relatorio-sus` já existe no GitHub, privado, e os commits já foram enviados. No passo de publicação do plano do autor, o comando passa a ser `gh repo edit JoaoEPGarcia/rag-relatorio-sus --visibility public --accept-visibility-change-consequences`, e não `gh repo create`.
- **Chave e Docker**: o `GEMINI_API_KEY` ainda não está no `.env`, e o Docker Desktop não está instalado. As duas coisas são passos manuais do autor, no roteiro do wizard.
- **Pontos de atenção da proposta do Gabarito** (para a Revisão):
  - 16 linhas trazem "ATENÇÃO" e 5 trazem "CONFERIR" (outras páginas com os mesmos valores);
  - a G43 depende de uma inconsistência do próprio relatório (η² = 0,43 no texto, 0,44 na tabela);
  - a G40 repete o 0,44% do Médio Porte cobrado na G10.
- **Frase de currículo** (passo de levar ao currículo): "Construí assistente com RAG (embeddings, banco vetorial, API em FastAPI e Docker) sobre relatório de 175 páginas e o avaliei com 60 perguntas: X% de acerto nas 50 respondíveis (IC 95%: a–b), contra Y% sem RAG". X, a, b e Y saem do registro de números.
- **Variabilidade**: o projeto não fixa `temperature`, então duas Rodadas iguais podem diferir. Por isso há as repetições, rotuladas como "Veredictos não revisados".

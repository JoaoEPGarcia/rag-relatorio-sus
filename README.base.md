# Assistente do relatório Gestão Hospitalar no SUS-SP: quanto dá para confiar nas respostas?

Um assistente que responde perguntas sobre um relatório de pesquisa em saúde pública, citando a página, e uma avaliação estatística da pergunta que importa antes de usar um assistente desses: **com que frequência ele acerta, e quanto disso vem da busca no documento?** As mesmas Perguntas, com resposta e página conferidas pelo autor no PDF, passam por três Condições: com RAG, sem RAG e com o relatório inteiro no contexto do modelo.

{{aviso_sintetico}}

| | |
|---|---|
| **Dados** | o relatório "Gestão Hospitalar no SUS-SP" ({{corpus_paginas}} páginas e {{corpus_palavras}} palavras extraídas), quebrado em {{corpus_trechos}} Trechos: {{corpus_trechos_texto}} de texto, {{corpus_trechos_tabela}} de tabela e {{corpus_trechos_legenda}} de legenda de figura |
| **Avaliação** | **{{gabarito_n_perguntas}} Perguntas** com resposta e página conferidas pelo autor no PDF: {{gabarito_n_respondiveis}} respondíveis, em {{gabarito_n_tipos}} Tipos (número na prosa, em tabela e em legenda, conceito e síntese entre páginas), e {{gabarito_n_sem_resposta}} sem resposta no Relatório-fonte |
| **Métodos** | intervalo de Wilson para cada taxa; teste exato de McNemar e intervalo de Newcombe para a diferença pareada entre Condições; Classes de erro derivadas das medidas; parâmetros congelados antes da Rodada principal |
| **Entrega** | API em FastAPI com Docker, e um Relatório de avaliação em LaTeX para público técnico |
| **Ferramentas** | Python (pdfplumber, fastembed, FAISS, FastAPI, API do Gemini, SciPy, matplotlib), pytest e LaTeX |

## Principais resultados

Os números abaixo são os da Rodada principal, analisada por `scripts/04_analisar.py` e detalhada no Relatório de avaliação (`relatorio/relatorio.pdf`). A fonte de cada número impresso está em `NUMEROS_CANONICOS.md`.

- **Acerto da resposta.** Com RAG, o assistente acerta **{{destaque_acerto_com_rag}}** das {{destaque_n_respondiveis}} Perguntas respondíveis (IC de {{ic_nivel}}%: {{destaque_acerto_com_rag_inf}} a {{destaque_acerto_com_rag_sup}}). Sem RAG, o mesmo modelo acerta {{destaque_acerto_sem_rag}} das mesmas Perguntas. A diferença pareada, com RAG menos sem RAG, é de **{{com_rag_x_sem_rag_diferenca}}** (IC de {{ic_nivel}}%: {{com_rag_x_sem_rag_diferenca_inf}} a {{com_rag_x_sem_rag_diferenca_sup}}): {{com_rag_x_sem_rag_conclusao}}.
- **Busca ou Relatório-fonte inteiro.** Com o Relatório-fonte inteiro no prompt, o acerto é de {{contexto_completo_acerto_resposta}} (IC de {{ic_nivel}}%: {{contexto_completo_acerto_resposta_inf}} a {{contexto_completo_acerto_resposta_sup}}). A diferença pareada, com RAG menos contexto completo, é de **{{com_rag_x_contexto_completo_diferenca}}** (IC de {{ic_nivel}}%: {{com_rag_x_contexto_completo_diferenca_inf}} a {{com_rag_x_contexto_completo_diferenca_sup}}): {{com_rag_x_contexto_completo_conclusao}}. Por Pergunta, o contexto completo lê em média {{contexto_completo_tokens_entrada_medio}} tokens de entrada e responde em {{contexto_completo_latencia_mediana_s}} s (mediana); com RAG, são {{com_rag_tokens_entrada_medio}} tokens e {{com_rag_latencia_mediana_s}} s.
- **Perguntas sem resposta.** Nas {{com_rag_n_sem_resposta}} Perguntas que o Relatório-fonte não responde, o assistente com RAG se abstém, como deve, em **{{com_rag_abstencao_correta}}** (IC de {{ic_nivel}}%: {{com_rag_abstencao_correta_inf}} a {{com_rag_abstencao_correta_sup}}); sem RAG, em {{sem_rag_abstencao_correta}}, e com o contexto completo, em {{contexto_completo_abstencao_correta}}.
- **Onde erra.** Com RAG, a Classe de erro mais frequente é {{com_rag_erro_mais_frequente}}, com **{{com_rag_erro_mais_frequente_n}}** das {{com_rag_n_com_erro}} respostas que erram o conteúdo, a página citada ou a Abstenção. O cruzamento com o Tipo de pergunta está no Relatório de avaliação.

## Como a avaliação foi feita

1. **Extração e quebra.** O texto sai do PDF página a página, com tabelas e legendas separadas do texto corrido, e é quebrado em Trechos que nunca atravessam a página. Cada Trecho guarda a página impressa no rodapé, que é a que se cita.
2. **Busca.** Os Trechos viram vetores com o modelo `multilingual-e5-large`, e a busca é exata (FAISS `IndexFlatIP`): a mesma Pergunta recupera sempre os mesmos Trechos ([ADR](docs/adr/0001-faiss-com-busca-exata.md)).
3. **Gabarito.** As Perguntas foram propostas a partir do texto e conferidas uma a uma pelo autor no PDF. O script de avaliação recusa rodar se alguma linha estiver sem Revisão.
4. **Condições.** O mesmo modelo (`gemini-3.5-flash-lite`, pelo Google AI Studio) responde às mesmas Perguntas com os Trechos recuperados (com RAG), sem nada do relatório (sem RAG) e com o texto inteiro no prompt (contexto completo).
5. **Veredicto.** As respostas numéricas são conferidas por regra; as descritivas, por um Juiz (modelo de linguagem), e todo Veredicto do Juiz passa pela Revisão do autor antes de valer.
6. **Pré-registro.** O número de Trechos recuperados, o tamanho do Trecho, o modelo e os prompts foram ajustados só com Perguntas de desenvolvimento e congelados por commit antes da Rodada principal ([ADR](docs/adr/0002-parametros-congelados-antes-da-rodada-principal.md)).

## Estrutura do repositório

| Caminho | O que é |
|---|---|
| `src/rag_sus/` | extração, quebra, busca, assistente, API e avaliação |
| `scripts/` | o pipeline, em passos numerados (`reproduzir.py` roda todos, menos as Rodadas, que chamam o modelo) |
| `avaliacao/` | Gabarito, Perguntas de desenvolvimento e folha de Revisão dos Veredictos |
| `resultados/` | Rodadas, registro de números e resumo da análise |
| `relatorio/` | Relatório de avaliação em LaTeX |
| `estilo/` | kit de estilo do portfólio (cópia, não editada) |
| `GLOSSARY.md`, `docs/adr/` | vocabulário do projeto e decisões difíceis de reverter |
| `NUMEROS_CANONICOS.md` | de onde sai cada número impresso |

## Como reproduzir

1. Instale o [uv](https://docs.astral.sh/uv/) e as dependências, `uv sync --all-groups`, e um LaTeX com o `pdflatex` (MiKTeX no Windows, TeX Live no Linux).
2. Refaça tudo a partir das Rodadas versionadas em `resultados/rodadas/`, sem chamar o modelo:
   ```
   uv run python scripts/reproduzir.py
   ```
   O comando extrai o PDF e constrói o índice, só se faltarem (na primeira vez, o índice baixa o modelo de embeddings). Depois, refaz a análise, as figuras, o README, as macros LaTeX e o `NUMEROS_CANONICOS.md`, compila o Relatório de avaliação e roda o conferidor de números e a conferência mecânica do Gabarito. Ele para no primeiro erro e diz em que passo parou. Sem a Rodada principal, ou com Veredicto do Juiz sem Revisão, ele para na análise, antes de escrever qualquer documento.
3. Para refazer as Rodadas, que chamam o Gemini, configure a máquina com o roteiro guiado `bash scripts/configurar_maquina.sh`. Ele cria a chave do Gemini, liga (se você quiser) os créditos do Google AI Pro (ou instala o Ollama e baixa o modelo), grava no `.env`, instala o Docker Desktop e testa a API no contêiner. O `.env` não vai para o git. Depois, rode a Rodada principal e o pipeline de novo:
   ```
   uv run python scripts/03_rodar_avaliacao.py --rodada principal --confirmar
   uv run python scripts/reproduzir.py
   ```
   A Rodada gasta a cota diária do Gemini (ou os créditos do Google AI Pro, se o projeto for pré-pago), e por isso o pipeline nunca a roda; sem `--confirmar`, ela só mostra quantas chamadas faria. Se a cota ou o saldo acabar no meio, ela para, e o mesmo comando continua de onde parou no dia seguinte.
4. Para ver o pipeline inteiro sem chave de API, sobre Rodadas sintéticas numa pasta temporária (no Git Bash):
   ```
   export RAG_SUS_RAIZ="$(mktemp -d)"
   uv run python scripts/gerar_rodadas_sinteticas.py
   uv run python scripts/reproduzir.py
   ```
   Os números dessas Rodadas são inventados; o README, o PDF e as figuras saem na pasta temporária, e nada chega a `resultados/`.
5. Para subir a API: `docker compose up --build` e abra `http://localhost:8000/docs`. Na primeira subida, o contêiner baixa o modelo de embeddings e constrói o índice.
6. Testes: `uv run pytest`.

## Limitações

- **Só o texto do PDF.** Os valores que existem apenas dentro da imagem de um gráfico não são extraídos; Perguntas que dependem deles ficaram fora do Gabarito.
- **Amostra pequena.** Com {{gabarito_n_perguntas}} Perguntas, os intervalos são largos: a avaliação distingue diferenças grandes entre Condições, mas não diferenças pequenas.
- **Um documento só.** O resultado vale para este relatório, com esta diagramação; outro documento pede outra avaliação.
- **Quem propôs o Gabarito.** As Perguntas foram propostas com ajuda de um modelo de linguagem e conferidas pelo autor; elas podem favorecer o que um modelo acha fácil de perguntar.

## Autoria

- **João Eduardo Pastori Garcia**: estatístico responsável. Concebeu a avaliação, revisou o Gabarito e os Veredictos no PDF e conduziu o projeto. [LinkedIn](https://www.linkedin.com/in/joao-eduardo-garcia/) · [GitHub](https://github.com/JoaoEPGarcia)

## In English

An assistant that answers questions about a public-health research report, citing the page, and a statistical evaluation of how often it is right with retrieval (RAG), without it, and with the whole report in the model's context.

{{aviso_sintetico:en}}

- **Data:** the report "Gestão Hospitalar no SUS-SP" ({{corpus_paginas:en}} pages, {{corpus_palavras:en}} words), split into {{corpus_trechos:en}} passages that never cross a page; {{gabarito_n_perguntas:en}} questions checked by the author against the PDF: {{gabarito_n_respondiveis:en}} answerable, in {{gabarito_n_tipos:en}} types, and {{gabarito_n_sem_resposta:en}} that the report does not answer.
- **Methods:** Wilson intervals, exact McNemar test and Newcombe's paired-difference interval; error classes derived from the metrics; parameters frozen before the main run.
- **Main findings** (the same numbers as above, with decimal points):
  - With RAG, the assistant answers **{{destaque_acerto_com_rag:en}}** of the {{destaque_n_respondiveis:en}} answerable questions correctly ({{ic_nivel:en}}% CI: {{destaque_acerto_com_rag_inf:en}} to {{destaque_acerto_com_rag_sup:en}}), against {{destaque_acerto_sem_rag:en}} for the same model without RAG. The paired difference, RAG minus no RAG, is **{{com_rag_x_sem_rag_diferenca:en}}** ({{ic_nivel:en}}% CI: {{com_rag_x_sem_rag_diferenca_inf:en}} to {{com_rag_x_sem_rag_diferenca_sup:en}}): {{com_rag_x_sem_rag_conclusao:en}}.
  - With the whole report in the prompt, accuracy is {{contexto_completo_acerto_resposta:en}} ({{ic_nivel:en}}% CI: {{contexto_completo_acerto_resposta_inf:en}} to {{contexto_completo_acerto_resposta_sup:en}}). The paired difference, RAG minus full context, is **{{com_rag_x_contexto_completo_diferenca:en}}** ({{ic_nivel:en}}% CI: {{com_rag_x_contexto_completo_diferenca_inf:en}} to {{com_rag_x_contexto_completo_diferenca_sup:en}}): {{com_rag_x_contexto_completo_conclusao:en}}. Per question, full context reads {{contexto_completo_tokens_entrada_medio:en}} input tokens on average and answers in {{contexto_completo_latencia_mediana_s:en}} s (median); with RAG, {{com_rag_tokens_entrada_medio:en}} tokens and {{com_rag_latencia_mediana_s:en}} s.
  - On the {{com_rag_n_sem_resposta:en}} questions the report does not answer, the assistant with RAG abstains, as it should, in **{{com_rag_abstencao_correta:en}}** of them ({{ic_nivel:en}}% CI: {{com_rag_abstencao_correta_inf:en}} to {{com_rag_abstencao_correta_sup:en}}); without RAG, in {{sem_rag_abstencao_correta:en}}, and with full context, in {{contexto_completo_abstencao_correta:en}}.
  - With RAG, the most frequent error class is {{com_rag_erro_mais_frequente:en}}, in **{{com_rag_erro_mais_frequente_n:en}}** of the {{com_rag_n_com_erro:en}} answers that get the content, the cited page or the abstention wrong.
- **Deliverable:** a FastAPI service in Docker and a technical evaluation report in LaTeX.

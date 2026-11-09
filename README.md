<!-- GERADO por scripts/06_gerar_documentos.py a partir de README.base.md. Não edite à mão. -->
# Assistente do relatório Gestão Hospitalar no SUS-SP: quanto dá para confiar nas respostas?

Um assistente que responde perguntas sobre um relatório de pesquisa em saúde pública, citando a página, e uma avaliação estatística da pergunta que importa antes de usar um assistente desses: **com que frequência ele acerta, e quanto disso vem da busca no documento?** As mesmas Perguntas, com resposta e página conferidas pelo autor no PDF, passam por três Condições: com RAG, sem RAG e com o relatório inteiro no contexto do modelo.

| | |
|---|---|
| **Dados** | o relatório "Gestão Hospitalar no SUS-SP" (174 páginas e 60.370 palavras extraídas), quebrado em 570 Trechos: 390 de texto, 71 de tabela e 109 de legenda de figura |
| **Avaliação** | Perguntas com resposta e página conferidas pelo autor no PDF, em cinco Tipos (número na prosa, em tabela e em legenda, conceito e síntese entre páginas), mais Perguntas sem resposta no relatório |
| **Métodos** | intervalo de Wilson para cada taxa; teste exato de McNemar e intervalo de Newcombe para a diferença pareada entre Condições; Classes de erro derivadas das medidas; parâmetros congelados antes da Rodada principal |
| **Entrega** | API em FastAPI com Docker, e um Relatório de avaliação em LaTeX para público técnico |
| **Ferramentas** | Python (pdfplumber, fastembed, FAISS, FastAPI, SDK da Anthropic, SciPy, matplotlib), pytest e LaTeX |

## Principais resultados

<!-- Os resultados entram aqui, por marcador, depois da Rodada principal (scripts/04_analisar.py). -->
A Rodada principal ainda não foi feita: o Gabarito está em Revisão. Esta seção será preenchida pelos scripts, com cada número tirado do registro `resultados/numeros.json` e listado em `NUMEROS_CANONICOS.md`.

## Como a avaliação foi feita

1. **Extração e quebra.** O texto sai do PDF página a página, com tabelas e legendas separadas do texto corrido, e é quebrado em Trechos que nunca atravessam a página. Cada Trecho guarda a página impressa no rodapé, que é a que se cita.
2. **Busca.** Os Trechos viram vetores com o modelo `multilingual-e5-large`, e a busca é exata (FAISS `IndexFlatIP`): a mesma Pergunta recupera sempre os mesmos Trechos ([ADR](docs/adr/0001-faiss-com-busca-exata.md)).
3. **Gabarito.** As Perguntas foram propostas a partir do texto e conferidas uma a uma pelo autor no PDF. O script de avaliação recusa rodar se alguma linha estiver sem Revisão.
4. **Condições.** O mesmo modelo (`claude-opus-5-5`) responde às mesmas Perguntas com os Trechos recuperados (com RAG), sem nada do relatório (sem RAG) e com o texto inteiro no prompt (contexto completo).
5. **Veredicto.** As respostas numéricas são conferidas por regra; as descritivas, por um Juiz (modelo de linguagem), e todo Veredicto do Juiz passa pela Revisão do autor antes de valer.
6. **Pré-registro.** O número de Trechos recuperados, o tamanho do Trecho, o modelo e os prompts foram ajustados só com Perguntas de desenvolvimento e congelados por commit antes da Rodada principal ([ADR](docs/adr/0002-parametros-congelados-antes-da-rodada-principal.md)).

## Estrutura do repositório

| Caminho | O que é |
|---|---|
| `src/rag_sus/` | extração, quebra, busca, assistente, API e avaliação |
| `scripts/` | o pipeline, em passos numerados (`rodar_tudo.py` roda todos) |
| `avaliacao/` | Gabarito, Perguntas de desenvolvimento e folha de Revisão dos Veredictos |
| `resultados/` | Rodadas, registro de números e resumo da análise |
| `relatorio/` | Relatório de avaliação em LaTeX |
| `estilo/` | kit de estilo do portfólio (cópia, não editada) |
| `GLOSSARY.md`, `docs/adr/` | vocabulário do projeto e decisões difíceis de reverter |
| `NUMEROS_CANONICOS.md` | de onde sai cada número impresso |

## Como reproduzir

1. Instale o [uv](https://docs.astral.sh/uv/) e as dependências: `uv sync --all-groups`.
2. Copie `.env.exemplo` para `.env` e preencha `ANTHROPIC_API_KEY`. O `.env` não vai para o git.
3. Rode o pipeline:
   ```
   uv run python scripts/01_extrair.py
   uv run python scripts/02_indexar.py
   uv run python scripts/03_rodar_avaliacao.py --rodada principal --confirmar
   uv run python scripts/04_analisar.py
   uv run python scripts/05_figuras.py
   uv run python scripts/06_gerar_documentos.py
   uv run python scripts/conferir_numeros.py
   ```
   O passo `03` chama a API da Anthropic e tem custo; sem `--confirmar`, ele só mostra quantas chamadas faria. As Rodadas já feitas estão versionadas em `resultados/rodadas/`, e os passos `04` a `06` refazem a análise a partir delas, sem custo.
4. Para subir a API: `docker compose up --build` e abra `http://localhost:8000/docs`. Na primeira subida, o contêiner baixa o modelo de embeddings e constrói o índice.
5. Testes: `uv run pytest`.

## Limitações

- **Só o texto do PDF.** Os valores que existem apenas dentro da imagem de um gráfico não são extraídos; Perguntas que dependem deles ficaram fora do Gabarito.
- **Amostra pequena.** Com dezenas de Perguntas, os intervalos são largos: a avaliação distingue diferenças grandes entre Condições, mas não diferenças pequenas.
- **Um documento só.** O resultado vale para este relatório, com esta diagramação; outro documento pede outra avaliação.
- **Quem propôs o Gabarito.** As Perguntas foram propostas com ajuda de um modelo de linguagem e conferidas pelo autor; elas podem favorecer o que um modelo acha fácil de perguntar.

## Autoria

- **João Eduardo Pastori Garcia**: estatístico responsável. Concebeu a avaliação, revisou o Gabarito e os Veredictos no PDF e conduziu o projeto. [LinkedIn](https://www.linkedin.com/in/joao-eduardo-garcia/) · [GitHub](https://github.com/JoaoEPGarcia)

## In English

An assistant that answers questions about a public-health research report, citing the page, and a statistical evaluation of how often it is right with retrieval (RAG), without it, and with the whole report in the model's context.

- **Data:** the report "Gestão Hospitalar no SUS-SP", split into 570 passages that never cross a page.
- **Methods:** Wilson intervals, exact McNemar test and Newcombe's paired-difference interval; error classes derived from the metrics; parameters frozen before the main run.
- **Deliverable:** a FastAPI service in Docker and a technical evaluation report in LaTeX.

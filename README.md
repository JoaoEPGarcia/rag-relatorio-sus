<!-- GERADO por scripts/06_gerar_documentos.py a partir de README.base.md. Não edite à mão. -->
# Assistente do relatório Gestão Hospitalar no SUS-SP: quanto dá para confiar nas respostas?

Um assistente que responde perguntas sobre um relatório de pesquisa em saúde pública, citando a página, e uma avaliação estatística da pergunta que importa antes de usar um assistente desses: **com que frequência ele acerta, e quanto disso vem da busca no documento?** As mesmas Perguntas, com resposta e página conferidas pelo autor no PDF, passam por três Condições: com RAG, sem RAG e com o relatório inteiro no contexto do modelo.



| | |
|---|---|
| **Dados** | o relatório "Gestão Hospitalar no SUS-SP" (174 páginas e 60.370 palavras extraídas), quebrado em 570 Trechos: 390 de texto, 71 de tabela e 109 de legenda de figura |
| **Avaliação** | **60 Perguntas** com resposta e página conferidas pelo autor no PDF: 50 respondíveis, em 5 Tipos (número na prosa, em tabela e em legenda, conceito e síntese entre páginas), e 10 sem resposta no Relatório-fonte |
| **Métodos** | intervalo de Wilson para cada taxa; teste exato de McNemar e intervalo de Newcombe para a diferença pareada entre Condições; Classes de erro derivadas das medidas; parâmetros congelados antes da Rodada principal |
| **Entrega** | API em FastAPI com Docker, e um Relatório de avaliação em LaTeX para público técnico |
| **Ferramentas** | Python (pdfplumber, fastembed, FAISS, FastAPI, API do Gemini, SciPy, matplotlib), pytest e LaTeX |

## Principais resultados

Os números abaixo são os da Rodada principal, analisada por `scripts/04_analisar.py` e detalhada no Relatório de avaliação (`relatorio/relatorio.pdf`). A fonte de cada número impresso está em `NUMEROS_CANONICOS.md`.

- **Acerto da resposta.** Com RAG, o assistente acerta **78,0%** das 50 Perguntas respondíveis (IC de 95%: 64,8% a 87,2%). Sem RAG, o mesmo modelo acerta 0,0% das mesmas Perguntas: em 50 delas, ele se abstém, em vez de inventar uma resposta. A diferença pareada, com RAG menos sem RAG, é de **78,0 p.p.** (IC de 95%: 63,0 p.p. a 87,2 p.p.): com RAG acerta mais.
- **Busca ou Relatório-fonte inteiro.** Com o Relatório-fonte inteiro no prompt, o acerto é de 98,0% (IC de 95%: 89,5% a 99,6%). A diferença pareada, com RAG menos contexto completo, é de **−20,0 p.p.** (IC de 95%: −33,5 p.p. a −7,0 p.p.): com RAG acerta menos. Por Pergunta, o contexto completo lê em média 99.197 tokens de entrada e responde em 6,1 s (mediana); com RAG, são 1.745 tokens e 3,2 s.
- **Perguntas sem resposta.** Nas 10 Perguntas que o Relatório-fonte não responde, o assistente com RAG se abstém, como deve, em **100,0%** (IC de 95%: 72,2% a 100,0%); sem RAG, em 100,0%, e com o contexto completo, em 100,0%.
- **Onde erra.** Com RAG, a Classe de erro mais frequente é abstenção indevida, com **5** das 13 respostas que erram o conteúdo, a página citada ou a Abstenção. O cruzamento com o Tipo de pergunta está no Relatório de avaliação.

## Como a avaliação foi feita

1. **Extração e quebra.** O texto sai do PDF página a página, com tabelas e legendas separadas do texto corrido, e é quebrado em Trechos que nunca atravessam a página. Cada Trecho guarda a página impressa no rodapé, que é a que se cita.
2. **Busca.** Os Trechos viram vetores com o modelo `multilingual-e5-large`, e a busca é exata (FAISS `IndexFlatIP`): a mesma Pergunta recupera sempre os mesmos Trechos ([ADR](docs/adr/0001-faiss-com-busca-exata.md)).
3. **Gabarito.** As Perguntas foram propostas a partir do texto e conferidas uma a uma pelo autor no PDF. O script de avaliação recusa rodar se alguma linha estiver sem Revisão.
4. **Condições.** O mesmo modelo (`gemini-3.5-flash-lite`, pelo Google AI Studio) responde às mesmas Perguntas com os Trechos recuperados (com RAG), sem nada do Relatório-fonte (sem RAG) e com o texto inteiro no prompt (contexto completo).
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
- **Amostra pequena.** Com 60 Perguntas, os intervalos são largos: a avaliação distingue diferenças grandes entre Condições, mas não diferenças pequenas.
- **Um documento só.** O resultado vale para este Relatório-fonte, com esta diagramação; outro documento pede outra avaliação.
- **Quem propôs o Gabarito.** As Perguntas foram propostas com ajuda de um modelo de linguagem e conferidas pelo autor; elas podem favorecer o que um modelo acha fácil de perguntar.

## Autoria

- **João Eduardo Pastori Garcia**: estatístico responsável. Concebeu a avaliação, revisou o Gabarito e os Veredictos no PDF e conduziu o projeto. [LinkedIn](https://www.linkedin.com/in/joao-eduardo-garcia/) · [GitHub](https://github.com/JoaoEPGarcia)

## In English

An assistant that answers questions about a public-health research report, citing the page, and a statistical evaluation of how often it is right with retrieval (RAG), without it, and with the whole report in the model's context.



- **Data:** the report "Gestão Hospitalar no SUS-SP" (174 pages, 60,370 words), split into 570 passages that never cross a page; 60 questions checked by the author against the PDF: 50 answerable, in 5 types, and 10 that the report does not answer.
- **Methods:** Wilson intervals, exact McNemar test and Newcombe's paired-difference interval; error classes derived from the metrics; parameters frozen before the main run.
- **Main findings** (the same numbers as above, with decimal points):
  - With RAG, the assistant answers **78.0%** of the 50 answerable questions correctly (95% CI: 64.8% to 87.2%), against 0.0% for the same model without RAG, which abstains on 50 of them instead of making up an answer. The paired difference, RAG minus no RAG, is **78.0 pp** (95% CI: 63.0 pp to 87.2 pp): RAG gets more answers right.
  - With the whole report in the prompt, accuracy is 98.0% (95% CI: 89.5% to 99.6%). The paired difference, RAG minus full context, is **−20.0 pp** (95% CI: −33.5 pp to −7.0 pp): RAG gets fewer answers right. Per question, full context reads 99,197 input tokens on average and answers in 6.1 s (median); with RAG, 1,745 tokens and 3.2 s.
  - On the 10 questions the report does not answer, the assistant with RAG abstains, as it should, in **100.0%** of them (95% CI: 72.2% to 100.0%); without RAG, in 100.0%, and with full context, in 100.0%.
  - With RAG, the most frequent error class is unwarranted abstention, in **5** of the 13 answers that get the content, the cited page or the abstention wrong.
- **Deliverable:** a FastAPI service in Docker and a technical evaluation report in LaTeX.

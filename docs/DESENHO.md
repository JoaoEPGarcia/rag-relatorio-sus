# Desenho do projeto

Decisões tomadas na entrevista de 09/11/2026. Os termos estão definidos em `GLOSSARY.md`, e as decisões difíceis de reverter, em `docs/adr/`.

## Objetivo

Um assistente que responde perguntas sobre o Relatório-fonte ("Gestão Hospitalar no SUS-SP", PDF de 175 páginas, com publicação autorizada) citando a Página. O diferencial é a avaliação estatística. O público é quem recruta para dados e ML (VTEX, iFood, Sezzle, Artefact).

## Pipeline

1. **Extração** (`pdfplumber`): o texto por página, com as tabelas detectadas à parte e normalização NFKC (por causa das ligaduras). Cada página guarda a página impressa e a página do PDF (ADR 0004). A capa fica fora.
2. **Quebra**: nenhum Trecho atravessa a fronteira de página. O texto é quebrado por parágrafo até um tamanho-alvo, com pequena sobreposição. O título da seção vai no início de cada Trecho. Cada tabela é serializada linha a linha num Trecho próprio, e cada legenda de figura também vira um Trecho próprio.
3. **Embeddings**: `multilingual-e5-large` via fastembed (ONNX, sem PyTorch).
4. **Busca**: FAISS `IndexFlatIP`, busca exata (ADR 0001). Só vetorial.
5. **Resposta**: Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) pelo Google AI Studio, no plano gratuito (ADR 0005), com raciocínio em nível `medium` e saída estruturada por JSON Schema (resposta, páginas citadas, abstenção). Cada resposta registra o modelo que de fato respondeu. Nada é pago além dos créditos do AI Pro. O Ollama é um provedor local alternativo, sem números publicados.
6. **API**: FastAPI, com `POST /perguntar` e a documentação do Swagger. Não há interface web nem deploy público.
7. **Docker**: `Dockerfile` e `docker-compose.yml`. O modelo de embeddings (2,24 GB) e o índice ficam em volumes e são criados na primeira subida, fora da imagem. O GitHub Actions constrói a imagem e roda os testes a cada push.

## Avaliação

- **Gabarito**: 60 Perguntas, das quais 50 são respondíveis (5 Tipos de pergunta × 10, espalhadas pelos capítulos em proporção ao volume de texto) e 10 são sem resposta. Eu proponho, e o autor revisa no PDF. O script de avaliação recusa rodar se alguma linha estiver sem Revisão.
- **Fora do Gabarito**: as perguntas cuja resposta só existe dentro da imagem de um gráfico. Essa exclusão é declarada nas limitações.
- **Condições**: com RAG, sem RAG e contexto completo (o texto inteiro no prompt, com cache). A comparação principal é com RAG × sem RAG. Também são medidos os tokens de entrada (a medida de custo, já que não há fatura em dólar) e a latência por Pergunta.
- **Número de destaque** (README e frase de currículo): o Acerto da resposta nas 50 Perguntas respondíveis, com IC de Wilson de 95%, contra o mesmo acerto sem RAG. Não se usa um "acerto geral" sobre as 60: sem RAG, abster-se de tudo inflaria essa taxa.
- **Medidas**: Acerto da resposta (a principal), Acerto da citação e Acerto da recuperação. Cada uma sai com o intervalo de Wilson de 95%. As Perguntas respondíveis e as sem resposta são relatadas em separado.
- **Comparação pareada**: teste exato de McNemar mais um intervalo de 95% para a diferença pareada.
- **Veredicto**: as respostas numéricas são pontuadas por regra determinística: todos os valores do Gabarito precisam aparecer na resposta, exatamente. Quando a regra aprova, o Veredicto está dado. Quando reprova, a resposta vai também ao Juiz, para pegar falso negativo da regra (por exemplo, "−0,62" contra "0,62 para baixo"). As descritivas vão sempre ao Juiz (`gemini-3.6-flash`, raciocínio `medium`, saída estruturada; quando a cota diária dele acaba, assume o reserva seguinte, ADR 0005). O autor revisa todos os Veredictos do Juiz na Rodada principal, numa folha CSV (`avaliacao/revisao_veredictos.csv`).
- **Páginas do Gabarito**: quando a mesma resposta aparece em mais de uma página (o sumário executivo e a conclusão repetem achados dos capítulos), o Gabarito lista todas, para que uma citação certa não conte como errada.
- **Repetições**: mais 2 Rodadas automáticas, só para medir a concordância entre Rodadas. Esse número fica rotulado como "Veredictos não revisados".
- **Classes de erro**: falha de recuperação, falha de leitura, abstenção indevida, resposta inventada e citação errada. São derivadas automaticamente das medidas e cruzadas com o Tipo de pergunta.
- **Pré-registro**: os parâmetros são congelados antes da Rodada principal, e os ajustes são feitos só com Perguntas de desenvolvimento (ADR 0002).

## Números e documentos

- Cada script grava os seus números em `resultados/numeros.json`. `scripts/06_gerar_documentos.py` gera a partir dele `relatorio/numeros.tex`, `NUMEROS_CANONICOS.md` (nas colunas do kit) e `README.md` (a partir de `README.base.md`, ADR 0003).
- Um conferidor falha se algum número do README ou do `.tex` não estiver no registro.
- O estilo vem do kit `Desktop/portfolio-estilo`, copiado para `estilo/` e nunca editado na cópia.
- O Relatório de avaliação é um relatório técnico curto, de 10 a 15 páginas, para público técnico, compilado com pdfLaTeX a partir de `modelo_relatorio.tex`.

## Convenções

- Código, comentários, docstrings e commits em português do Brasil. A docstring diz o "por quê".
- `uv`, `pyproject.toml`, `uv.lock`, Python 3.12 e `ruff`. Testes em pytest, escritos com TDD nos módulos de quebra, busca e avaliação.
- As credenciais ficam só no `.env`, fora do git. O modelo do arquivo está em `.env.exemplo`.
- O repositório fica privado até a entrega e só fica público com a confirmação do autor.

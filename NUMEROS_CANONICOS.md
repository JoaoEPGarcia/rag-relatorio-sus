# Números canônicos

Cada número impresso no README, no Relatório de avaliação ou numa figura tem uma linha aqui, com o script que o calcula e os lugares onde aparece.

**Arquivo gerado** por `scripts/06_gerar_documentos.py` a partir de `resultados/numeros.json`. Não edite à mão. Para mudar um número, mude o script da coluna "Sai de", rode o pipeline (`uv run python scripts/rodar_tudo.py`) e confira cada lugar da coluna "Onde aparece".

| Número | Valor | O que é | Sai de | Onde aparece |
|---|---|---|---|---|
| `\NumCorpusLegendas` | 104 | legendas de figura extraídas | `scripts/01_extrair.py` | (não impresso) |
| `\NumCorpusPaginas` | 174 | páginas do Relatório-fonte no corpus (sem a capa) | `scripts/01_extrair.py` | README |
| `\NumCorpusPalavras` | 60.370 | palavras extraídas do Relatório-fonte | `scripts/01_extrair.py` | README |
| `\NumCorpusTabelas` | 28 | tabelas extraídas (blocos de tabela) | `scripts/01_extrair.py` | (não impresso) |
| `\NumCorpusTrechos` | 570 | Trechos indexados | `scripts/01_extrair.py` | README |
| `\NumCorpusTrechosLegenda` | 109 | Trechos de legenda de figura | `scripts/01_extrair.py` | README |
| `\NumCorpusTrechosTabela` | 71 | Trechos de tabela | `scripts/01_extrair.py` | README |
| `\NumCorpusTrechosTexto` | 390 | Trechos de texto corrido | `scripts/01_extrair.py` | README |
| `\NumQuebraAlvo` | 180 | máximo de palavras por Trecho de texto | `scripts/01_extrair.py` | (não impresso) |
| `\NumQuebraSobreposicao` | 30 | máximo de palavras repetidas entre Trechos vizinhos | `scripts/01_extrair.py` | (não impresso) |

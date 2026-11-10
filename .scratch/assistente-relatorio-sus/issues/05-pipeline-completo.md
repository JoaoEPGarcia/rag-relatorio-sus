# 05: Pipeline completo

**What to build:** quem clona o repositório refaz tudo com um comando, sem pagar a API e a partir das Rodadas versionadas. O comando para no primeiro erro e força UTF-8 na saída do Windows. A ordem:

1. extração e índice, só se faltarem;
2. análise;
3. figuras;
4. documentos (macros, `NUMEROS_CANONICOS.md`, README);
5. compilação do Relatório de avaliação;
6. conferidor de números;
7. conferência mecânica do Gabarito.

A Rodada paga nunca roda por esse comando. O README passa a citar o comando em "Como reproduzir".

**Blocked by:** 02 (Figuras), 03 (Relatório de avaliação), 04 (Resultados no README)

**Status:** resolved

- [x] Sobre a raiz sintética, o comando roda do início ao fim e termina com o conferidor "ok".
- [x] Uma falha num passo interrompe o pipeline, com código de saída diferente de zero e o nome do passo que falhou.
- [x] Sem Rodada principal consolidável (faltando Revisão), o pipeline para na análise com a mensagem da trava, sem gerar documento parcial.
- [x] O CI continua verde.

## Comments

Resolvido na branch `integracao/assistente-relatorio-sus` (09/11/2026). Comando: `uv run python scripts/reproduzir.py` (lógica em `src/rag_sus/pipeline.py`). Sobre a raiz sintética, termina com "Conferência dos números: ok". No checkout real, para no passo «análise» (código 1) porque falta a Rodada principal. O `.tex` é lido do projeto e compilado com o diretório de trabalho em `RAIZ/relatorio`. O teste de ponta a ponta é `lento` e é pulado sem pdflatex.

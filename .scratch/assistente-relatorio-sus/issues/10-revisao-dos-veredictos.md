# 10: Revisão dos Veredictos

**What to build:** o autor abre a folha de Revisão dos Veredictos (CSV) e, para cada resposta que o Juiz julgou, compara a resposta com o Gabarito e preenche `veredicto_revisado` com "certo" ou "errado", com comentário quando discordar do Juiz. Regravar a folha preserva o que já foi revisado.

**Blocked by:** 09 (Rodada principal e repetições)

**Status:** resolved

- [x] Todos os Veredictos do Juiz da Rodada principal têm `veredicto_revisado` preenchido com "certo" ou "errado".
- [x] A consolidação da Rodada principal deixa de recusar por falta de Revisão.

## Comments

Resolvido em 10/11/2026. O autor leu os 42 Veredictos do Juiz da Rodada principal na folha em PDF (`scripts/gerar_folha_dos_veredictos.py`) e concordou com todos: "o que estava correto realmente era correto e o que julgou como errado realmente estava errado". Por isso, `veredicto_revisado` repete `veredicto_juiz` em todas as linhas, sem comentário. Ficaram certos 15 com RAG e 20 no contexto completo, e errados 6 com RAG e 1 no contexto completo. A consolidação das três Condições passa com `exigir_revisao=True`.


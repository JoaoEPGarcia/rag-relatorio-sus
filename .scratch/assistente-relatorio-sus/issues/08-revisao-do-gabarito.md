# 08: Revisão do Gabarito

**What to build:** o autor confere no PDF cada uma das 60 linhas propostas do Gabarito: pergunta inequívoca, resposta, valores e todas as páginas impressas em que a resposta aparece. Então preenche a coluna `revisado` com as suas iniciais e a data.

As linhas marcadas "ATENÇÃO" (16) trazem dúvidas da extração, e as marcadas "CONFERIR" (5) trazem outras páginas com os mesmos valores. Duas linhas são candidatas a troca:

- G43, que depende da inconsistência η² = 0,43 no texto contra 0,44 na tabela;
- G40, que repete o 0,44% do Médio Porte da G10.

Uma Pergunta trocada continua respeitando os tipos e a distribuição (5 Tipos × 10, mais 10 sem resposta).

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Todas as 60 linhas têm `revisado` preenchido.
- [x] A conferência mecânica do Gabarito passa sem problema.
- [x] A distribuição continua 10 por Tipo de pergunta, mais 10 sem resposta.
- [x] As Perguntas sem resposta foram confirmadas como ausentes do relatório.

## Comments

Resolvido em 10/11/2026. O autor conferiu as 60 linhas no PDF, pela folha de Revisão (`scripts/gerar_folha_do_gabarito.py`), e respondeu: "aprovo todos [...] após ler todas julgo as respostas muito boas, claro tem um ponto de atenção aqui e ali mas no geral eu aprovo todas". Ele citou "D08", que não existe no Gabarito; foi lido como G08, uma das linhas "ATENÇÃO", e a aprovação vale para ela de qualquer modo.

- Nenhuma linha foi corrigida nem trocada. As candidatas G43 (η² de 0,43 no texto contra 0,44 na tabela) e G40 (repete o 0,44% da G10) ficam como estão, por decisão do autor.
- `revisado` preenchido com "JEPG 10/11/2026" em todas as linhas. O autor não mandou as iniciais, e o agente usou as do autor do repositório.
- `scripts/conferir_gabarito.py`: 60 linhas, 60 revisadas, 0 problemas mecânicos. Continua com 10 Perguntas por Tipo, mais 10 sem resposta.


# 02: Figuras

**What to build:** quem abre o README ou o Relatório de avaliação vê três figuras no estilo do portfólio, cada uma com o título afirmando o achado:

1. Acerto da resposta por Condição, com o intervalo de Wilson. Com RAG sai em destaque, e as demais em neutro.
2. Classes de erro por Tipo de pergunta, na Condição com RAG.
3. Tokens de entrada e latência por Pergunta contra o acerto, por Condição, para responder ao "se cabe no contexto, para que RAG?".

Os números dos títulos e rótulos vêm do registro, por f-string. O script registra cada número que imprime, declarando em que figura ele aparece. A figura segue o `GUIA_ESTILO.md` do kit copiado em `estilo/`:

- rótulo direto, e não legenda;
- uma cor de destaque e o resto neutro;
- barra no zero e sem eixo duplo;
- vírgula decimal;
- fonte no rodapé;
- boxplot, e nunca violino, se houver distribuição.

**Blocked by:** 01 (Da Rodada aos números)

**Status:** resolved

- [x] Sobre as Rodadas sintéticas do ticket 01, numa raiz temporária, o script gera as três PNG sem erro.
- [x] Cada número impresso numa figura está no registro, com a figura na coluna "Onde aparece" do `NUMEROS_CANONICOS.md`.
- [x] `python estilo/estilo_portfolio.py --validar` passa (ou passa com as ressalvas declaradas).
- [x] As figuras foram conferidas contra o checklist da skill chartosaur-viz e o "Antes de entregar" do guia.
- [x] Nenhum número sintético chega ao registro real nem às figuras versionadas.

## Comments

Resolvido na branch `integracao/assistente-relatorio-sus` (09/11/2026). `scripts/05_figuras.py` (lógica em `avaliacao/figuras.py`) gera `acerto_por_condicao.png`, `erros_por_tipo.png` e `custo_por_condicao.png`. Os títulos escolhem a frase pelo IC da diferença pareada e nunca afirmam proximidade quando o IC inclui zero. As figuras declaram os usos das chaves de origem (`numeros.declarar_usos`), que aparecem em "Onde aparece". `--validar` passa com as duas ressalvas padrão do kit. Checklists do GUIA e do chartosaur-viz conferidos sobre a raiz sintética, com uma ressalva: as Condições neutras também têm rótulo direto, em cinza e peso regular.

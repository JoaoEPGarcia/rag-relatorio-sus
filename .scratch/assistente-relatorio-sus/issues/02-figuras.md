# 02: Figuras

**What to build:** quem abre o README ou o Relatório de avaliação vê três figuras no estilo do portfólio, cada uma com o título afirmando o achado:

1. Acerto da resposta por Condição, com o intervalo de Wilson. Com RAG sai em destaque, e as demais em neutro.
2. Classes de erro por Tipo de pergunta, na Condição com RAG.
3. Custo e latência por Pergunta contra o acerto, por Condição, para responder ao "se cabe no contexto, para que RAG?".

Os números dos títulos e rótulos vêm do registro, por f-string. O script registra cada número que imprime, declarando em que figura ele aparece. A figura segue o `GUIA_ESTILO.md` do kit copiado em `estilo/`:

- rótulo direto, e não legenda;
- uma cor de destaque e o resto neutro;
- barra no zero e sem eixo duplo;
- vírgula decimal;
- fonte no rodapé;
- boxplot, e nunca violino, se houver distribuição.

**Blocked by:** 01 (Da Rodada aos números)

**Status:** ready-for-agent

- [ ] Sobre as Rodadas sintéticas do ticket 01, numa raiz temporária, o script gera as três PNG sem erro.
- [ ] Cada número impresso numa figura está no registro, com a figura na coluna "Onde aparece" do `NUMEROS_CANONICOS.md`.
- [ ] `python estilo/estilo_portfolio.py --validar` passa (ou passa com as ressalvas declaradas).
- [ ] As figuras foram conferidas contra o checklist da skill chartosaur-viz e o "Antes de entregar" do guia.
- [ ] Nenhum número sintético chega ao registro real nem às figuras versionadas.

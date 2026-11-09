# 03: Relatório de avaliação em LaTeX

**What to build:** um entrevistador técnico lê um Relatório de avaliação curto, de 10 a 15 páginas, com o visual dos outros projetos do portfólio. A estrutura:

- cópia do `modelo_relatorio.tex` do kit, sem editar o bloco do preâmbulo;
- capa azul e vermelha com João Eduardo Pastori Garcia, estatístico responsável, LinkedIn `joao-eduardo-garcia` e GitHub `JoaoEPGarcia`;
- seções: problema; pipeline; desenho da avaliação (Gabarito e Revisão, Condições, medidas, pré-registro); resultados com intervalos; comparação pareada; erros por Tipo de pergunta; tokens e latência; variabilidade entre Rodadas; limitações.

Regras de composição:

- os números entram só por macro (`\input` do arquivo gerado) e as tabelas por `\linhasde`;
- no máximo uma caixa de destaque por seção;
- as figuras do ticket 02 entram com `\imagemplena`.

O texto declara que as Perguntas foram propostas com ajuda de um modelo e conferidas pelo autor.

**Blocked by:** 01 (Da Rodada aos números), 02 (Figuras)

**Status:** ready-for-agent

- [ ] Compila com pdfLaTeX (duas ou três passadas) sobre a raiz sintética, sem erro e sem referência indefinida.
- [ ] O conferidor de números passa: nenhum número digitado no texto corrido, e toda macro `\Num...` usada está definida.
- [ ] O preâmbulo do kit está intacto (diff vazio contra o modelo nesse bloco).
- [ ] As limitações citam: só texto (gráficos fora), amostra pequena, um documento, Gabarito proposto com ajuda de um modelo, e o número de Veredictos revisados.
- [ ] O PDF da raiz sintética não é versionado; o PDF versionado só será gerado no ticket 11.

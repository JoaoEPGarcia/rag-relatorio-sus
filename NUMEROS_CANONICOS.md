# Números canônicos

Cada número impresso no README, no Relatório de avaliação ou numa figura tem uma linha aqui, com o script que o calcula e os lugares onde aparece.

**Arquivo gerado** por `scripts/06_gerar_documentos.py` a partir de `resultados/numeros.json`. Não edite à mão. Para mudar um número, mude o script da coluna "Sai de", rode o pipeline (`uv run python scripts/reproduzir.py`) e confira cada lugar da coluna "Onde aparece".

| Número | Valor | O que é | Sai de | Onde aparece |
|---|---|---|---|---|
| `\NumAvisoSintetico` |  | aviso de números inventados, só sobre Rodadas sintéticas (senão, vazio) | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumComRagAbstencaoCorreta` | 100,0% | Abstenção correta com RAG (sem resposta) | `scripts/04_analisar.py` | README, relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAbstencaoCorretaInf` | 72,2% | Abstenção correta com RAG (sem resposta): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | README, relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAbstencaoCorretaSup` | 100,0% | Abstenção correta com RAG (sem resposta): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | README, relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAbstencoesCorretas` | 10 | Abstenções corretas com RAG (sem resposta) | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagAcertoCitacao` | 82,0% | Acerto da citação com RAG (respondíveis) | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAcertoCitacaoInf` | 69,2% | Acerto da citação com RAG (respondíveis): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAcertoCitacaoSup` | 90,2% | Acerto da citação com RAG (respondíveis): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAcertoRecuperacao` | 86,0% | Acerto da recuperação com RAG (respondíveis) | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAcertoRecuperacaoInf` | 73,8% | Acerto da recuperação com RAG (respondíveis): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAcertoRecuperacaoSup` | 93,0% | Acerto da recuperação com RAG (respondíveis): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumComRagAcertoResposta` | 78,0% | Acerto da resposta com RAG (respondíveis) | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png, figuras/custo_por_condicao.png |
| `\NumComRagAcertoRespostaInf` | 64,8% | Acerto da resposta com RAG (respondíveis): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png |
| `\NumComRagAcertoRespostaSup` | 87,2% | Acerto da resposta com RAG (respondíveis): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png |
| `\NumComRagAcertosCitacao` | 41 | acertos da citação com RAG (respondíveis) | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagAcertosRecuperacao` | 43 | acertos da recuperação com RAG (respondíveis) | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagAcertosResposta` | 39 | acertos da resposta com RAG (respondíveis) | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagErroMaisFrequente` | abstenção indevida | Classe de erro mais frequente com RAG (empates juntos) | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumComRagErroMaisFrequenteN` | 5 | respostas com RAG na Classe de erro mais frequente | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumComRagErrosAbstencaoIndevida` | 5 | Classe de erro 'abstenção indevida' com RAG (Perguntas) | `scripts/04_analisar.py` | figuras/erros_por_tipo.png |
| `\NumComRagErrosCitacaoErrada` | 2 | Classe de erro 'citação errada' com RAG (Perguntas) | `scripts/04_analisar.py` | figuras/erros_por_tipo.png |
| `\NumComRagErrosFalhaLeitura` | 4 | Classe de erro 'falha de leitura' com RAG (Perguntas) | `scripts/04_analisar.py` | figuras/erros_por_tipo.png |
| `\NumComRagErrosFalhaRecuperacao` | 2 | Classe de erro 'falha de recuperação' com RAG (Perguntas) | `scripts/04_analisar.py` | figuras/erros_por_tipo.png |
| `\NumComRagErrosRespostaInventada` | 0 | Classe de erro 'resposta inventada' com RAG (Perguntas) | `scripts/04_analisar.py` | figuras/erros_por_tipo.png |
| `\NumComRagLatenciaMedianaS` | 3,2 | latência mediana por Pergunta com RAG, em segundos | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/custo_por_condicao.tex, figuras/custo_por_condicao.png |
| `\NumComRagNComErro` | 13 | respostas com RAG com alguma Classe de erro (respondíveis e sem resposta) | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumComRagNFallback` | 0 | respostas com RAG dadas por outro modelo (fallback do servidor) | `scripts/04_analisar.py` | relatorio/tabelas/custo_por_condicao.tex |
| `\NumComRagNRespondiveis` | 50 | Perguntas respondíveis na Condição com RAG | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagNSemResposta` | 10 | Perguntas sem resposta na Condição com RAG | `scripts/04_analisar.py` | README |
| `\NumComRagTipoConceitoAbstencaoIndevida` | 0 | 'abstenção indevida' com RAG, Tipo 'Conceito ou método' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoConceitoAcertos` | 9 | acertos da resposta com RAG, Tipo 'Conceito ou método' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoConceitoCitacaoErrada` | 1 | 'citação errada' com RAG, Tipo 'Conceito ou método' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoConceitoFalhaLeitura` | 1 | 'falha de leitura' com RAG, Tipo 'Conceito ou método' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoConceitoFalhaRecuperacao` | 0 | 'falha de recuperação' com RAG, Tipo 'Conceito ou método' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoConceitoN` | 10 | Perguntas do Tipo 'Conceito ou método' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoNumeroLegendaAbstencaoIndevida` | 1 | 'abstenção indevida' com RAG, Tipo 'Número em legenda' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoNumeroLegendaAcertos` | 9 | acertos da resposta com RAG, Tipo 'Número em legenda' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroLegendaCitacaoErrada` | 0 | 'citação errada' com RAG, Tipo 'Número em legenda' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroLegendaFalhaLeitura` | 0 | 'falha de leitura' com RAG, Tipo 'Número em legenda' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroLegendaFalhaRecuperacao` | 0 | 'falha de recuperação' com RAG, Tipo 'Número em legenda' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroLegendaN` | 10 | Perguntas do Tipo 'Número em legenda' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoNumeroProsaAbstencaoIndevida` | 1 | 'abstenção indevida' com RAG, Tipo 'Número na prosa' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoNumeroProsaAcertos` | 9 | acertos da resposta com RAG, Tipo 'Número na prosa' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroProsaCitacaoErrada` | 0 | 'citação errada' com RAG, Tipo 'Número na prosa' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroProsaFalhaLeitura` | 0 | 'falha de leitura' com RAG, Tipo 'Número na prosa' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroProsaFalhaRecuperacao` | 0 | 'falha de recuperação' com RAG, Tipo 'Número na prosa' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroProsaN` | 10 | Perguntas do Tipo 'Número na prosa' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoNumeroTabelaAbstencaoIndevida` | 3 | 'abstenção indevida' com RAG, Tipo 'Número em tabela' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoNumeroTabelaAcertos` | 7 | acertos da resposta com RAG, Tipo 'Número em tabela' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroTabelaCitacaoErrada` | 1 | 'citação errada' com RAG, Tipo 'Número em tabela' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoNumeroTabelaFalhaLeitura` | 0 | 'falha de leitura' com RAG, Tipo 'Número em tabela' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroTabelaFalhaRecuperacao` | 0 | 'falha de recuperação' com RAG, Tipo 'Número em tabela' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoNumeroTabelaN` | 10 | Perguntas do Tipo 'Número em tabela' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoSemRespostaAcertos` | 10 | abstenções corretas com RAG nas Perguntas sem resposta | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoSemRespostaN` | 10 | Perguntas sem resposta | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoSemRespostaRespostaInventada` | 0 | 'resposta inventada' com RAG nas Perguntas sem resposta | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoSinteseAbstencaoIndevida` | 0 | 'abstenção indevida' com RAG, Tipo 'Síntese entre páginas' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoSinteseAcertos` | 5 | acertos da resposta com RAG, Tipo 'Síntese entre páginas' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoSinteseCitacaoErrada` | 0 | 'citação errada' com RAG, Tipo 'Síntese entre páginas' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex |
| `\NumComRagTipoSinteseFalhaLeitura` | 3 | 'falha de leitura' com RAG, Tipo 'Síntese entre páginas' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoSinteseFalhaRecuperacao` | 2 | 'falha de recuperação' com RAG, Tipo 'Síntese entre páginas' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTipoSinteseN` | 10 | Perguntas do Tipo 'Síntese entre páginas' | `scripts/04_analisar.py` | relatorio/tabelas/erros_por_tipo.tex, figuras/erros_por_tipo.png |
| `\NumComRagTokensCacheLeituraTotal` | 0 | tokens de entrada lidos do cache com RAG, soma da Rodada | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagTokensEntradaMedio` | 1.745 | tokens de entrada com RAG, média por Pergunta | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/custo_por_condicao.tex, figuras/custo_por_condicao.png |
| `\NumComRagTokensEntradaTotal` | 104.674 | tokens de entrada com RAG, soma da Rodada | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagTokensSaidaTotal` | 40.528 | tokens de saída com RAG, soma da Rodada | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagXContextoCompletoAmbos` | 38 | com RAG × contexto completo: as duas Condições acertam | `scripts/04_analisar.py` | relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXContextoCompletoConclusao` | com RAG acerta menos | com RAG × contexto completo: leitura do IC de Newcombe (todo acima, todo abaixo de zero ou incluindo o zero) | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumComRagXContextoCompletoDiferenca` | −20,0 p.p. | com RAG × contexto completo: diferença pareada do Acerto da resposta | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXContextoCompletoDiferencaInf` | −33,5 p.p. | com RAG × contexto completo: limite inferior do IC de Newcombe de 95% | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXContextoCompletoDiferencaSup` | −7,0 p.p. | com RAG × contexto completo: limite superior do IC de Newcombe de 95% | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXContextoCompletoNPares` | 50 | com RAG × contexto completo: Perguntas respondíveis pareadas | `scripts/04_analisar.py` | (não impresso) |
| `\NumComRagXContextoCompletoNenhum` | 0 | com RAG × contexto completo: as duas Condições erram | `scripts/04_analisar.py` | relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXContextoCompletoPMcnemar` | 0,006 | com RAG × contexto completo: valor-p do teste exato de McNemar | `scripts/04_analisar.py` | relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXContextoCompletoSoComRag` | 1 | com RAG × contexto completo: só com RAG acerta | `scripts/04_analisar.py` | relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXContextoCompletoSoContextoCompleto` | 11 | com RAG × contexto completo: só contexto completo acerta | `scripts/04_analisar.py` | relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXSemRagAmbos` | 0 | com RAG × sem RAG: as duas Condições acertam | `scripts/04_analisar.py` | relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXSemRagConclusao` | com RAG acerta mais | com RAG × sem RAG: leitura do IC de Newcombe (todo acima, todo abaixo de zero ou incluindo o zero) | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumComRagXSemRagDiferenca` | 78,0 p.p. | com RAG × sem RAG: diferença pareada do Acerto da resposta | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXSemRagDiferencaInf` | 63,0 p.p. | com RAG × sem RAG: limite inferior do IC de Newcombe de 95% | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXSemRagDiferencaSup` | 87,2 p.p. | com RAG × sem RAG: limite superior do IC de Newcombe de 95% | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXSemRagNPares` | 50 | com RAG × sem RAG: Perguntas respondíveis pareadas | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumComRagXSemRagNenhum` | 11 | com RAG × sem RAG: as duas Condições erram | `scripts/04_analisar.py` | relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXSemRagPMcnemar` | < 0,001 | com RAG × sem RAG: valor-p do teste exato de McNemar | `scripts/04_analisar.py` | relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXSemRagSoComRag` | 39 | com RAG × sem RAG: só com RAG acerta | `scripts/04_analisar.py` | relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumComRagXSemRagSoSemRag` | 0 | com RAG × sem RAG: só sem RAG acerta | `scripts/04_analisar.py` | relatorio/relatorio.tex, relatorio/tabelas/comparacao_pareada.tex |
| `\NumConcordanciaRepeticaoUmComRag` | 96,7% | concordância entre a Rodada principal e a repeticao1, com RAG (Veredictos não revisados) | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoUmComRagN` | 60 | Perguntas comparadas na concordância entre a Rodada principal e a repeticao1, com RAG | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoUmContextoCompleto` | 95,0% | concordância entre a Rodada principal e a repeticao1, contexto completo (Veredictos não revisados) | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoUmContextoCompletoN` | 60 | Perguntas comparadas na concordância entre a Rodada principal e a repeticao1, contexto completo | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoUmSemRag` | 100,0% | concordância entre a Rodada principal e a repeticao1, sem RAG (Veredictos não revisados) | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoUmSemRagN` | 60 | Perguntas comparadas na concordância entre a Rodada principal e a repeticao1, sem RAG | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoDoisComRag` | 95,0% | concordância entre a Rodada principal e a repeticao2, com RAG (Veredictos não revisados) | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoDoisComRagN` | 60 | Perguntas comparadas na concordância entre a Rodada principal e a repeticao2, com RAG | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoDoisContextoCompleto` | 96,7% | concordância entre a Rodada principal e a repeticao2, contexto completo (Veredictos não revisados) | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoDoisContextoCompletoN` | 60 | Perguntas comparadas na concordância entre a Rodada principal e a repeticao2, contexto completo | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoDoisSemRag` | 100,0% | concordância entre a Rodada principal e a repeticao2, sem RAG (Veredictos não revisados) | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumConcordanciaRepeticaoDoisSemRagN` | 60 | Perguntas comparadas na concordância entre a Rodada principal e a repeticao2, sem RAG | `scripts/04_analisar.py` | relatorio/tabelas/concordancia.tex |
| `\NumContextoCompletoAbstencaoCorreta` | 100,0% | Abstenção correta contexto completo (sem resposta) | `scripts/04_analisar.py` | README, relatorio/tabelas/resultados_por_condicao.tex |
| `\NumContextoCompletoAbstencaoCorretaInf` | 72,2% | Abstenção correta contexto completo (sem resposta): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumContextoCompletoAbstencaoCorretaSup` | 100,0% | Abstenção correta contexto completo (sem resposta): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumContextoCompletoAbstencoesCorretas` | 10 | Abstenções corretas contexto completo (sem resposta) | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoAcertoCitacao` | 86,0% | Acerto da citação contexto completo (respondíveis) | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumContextoCompletoAcertoCitacaoInf` | 73,8% | Acerto da citação contexto completo (respondíveis): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumContextoCompletoAcertoCitacaoSup` | 93,0% | Acerto da citação contexto completo (respondíveis): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumContextoCompletoAcertoResposta` | 98,0% | Acerto da resposta contexto completo (respondíveis) | `scripts/04_analisar.py` | README, relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png, figuras/custo_por_condicao.png |
| `\NumContextoCompletoAcertoRespostaInf` | 89,5% | Acerto da resposta contexto completo (respondíveis): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | README, relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png |
| `\NumContextoCompletoAcertoRespostaSup` | 99,6% | Acerto da resposta contexto completo (respondíveis): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | README, relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png |
| `\NumContextoCompletoAcertosCitacao` | 43 | acertos da citação contexto completo (respondíveis) | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoAcertosResposta` | 49 | acertos da resposta contexto completo (respondíveis) | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoErrosAbstencaoIndevida` | 0 | Classe de erro 'abstenção indevida' contexto completo (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoErrosCitacaoErrada` | 6 | Classe de erro 'citação errada' contexto completo (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoErrosFalhaLeitura` | 1 | Classe de erro 'falha de leitura' contexto completo (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoErrosFalhaRecuperacao` | 0 | Classe de erro 'falha de recuperação' contexto completo (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoErrosRespostaInventada` | 0 | Classe de erro 'resposta inventada' contexto completo (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoLatenciaMedianaS` | 6,1 | latência mediana por Pergunta contexto completo, em segundos | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/custo_por_condicao.tex, figuras/custo_por_condicao.png |
| `\NumContextoCompletoNFallback` | 0 | respostas contexto completo dadas por outro modelo (fallback do servidor) | `scripts/04_analisar.py` | relatorio/tabelas/custo_por_condicao.tex |
| `\NumContextoCompletoNRespondiveis` | 50 | Perguntas respondíveis na Condição contexto completo | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoNSemResposta` | 10 | Perguntas sem resposta na Condição contexto completo | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoTokensCacheLeituraTotal` | 0 | tokens de entrada lidos do cache contexto completo, soma da Rodada | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumContextoCompletoTokensEntradaMedio` | 99.197 | tokens de entrada contexto completo, média por Pergunta | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, relatorio/tabelas/custo_por_condicao.tex, figuras/custo_por_condicao.png |
| `\NumContextoCompletoTokensEntradaTotal` | 5.951.819 | tokens de entrada contexto completo, soma da Rodada | `scripts/04_analisar.py` | (não impresso) |
| `\NumContextoCompletoTokensSaidaTotal` | 66.270 | tokens de saída contexto completo, soma da Rodada | `scripts/04_analisar.py` | (não impresso) |
| `\NumCorpusLegendas` | 104 | legendas de figura extraídas | `scripts/01_extrair.py` | relatorio/relatorio.tex |
| `\NumCorpusPaginas` | 174 | páginas do Relatório-fonte no corpus (sem a capa) | `scripts/01_extrair.py` | README, relatorio/relatorio.tex |
| `\NumCorpusPalavras` | 60.370 | palavras extraídas do Relatório-fonte | `scripts/01_extrair.py` | README, relatorio/relatorio.tex |
| `\NumCorpusTabelas` | 28 | tabelas extraídas (blocos de tabela) | `scripts/01_extrair.py` | relatorio/relatorio.tex |
| `\NumCorpusTrechos` | 570 | Trechos indexados | `scripts/01_extrair.py` | README, relatorio/relatorio.tex |
| `\NumCorpusTrechosLegenda` | 109 | Trechos de legenda de figura | `scripts/01_extrair.py` | README, relatorio/relatorio.tex |
| `\NumCorpusTrechosTabela` | 71 | Trechos de tabela | `scripts/01_extrair.py` | README, relatorio/relatorio.tex |
| `\NumCorpusTrechosTexto` | 390 | Trechos de texto corrido | `scripts/01_extrair.py` | README, relatorio/relatorio.tex |
| `\NumDestaqueAcertoComRag` | 78,0% | destaque: Acerto da resposta com RAG (respondíveis) | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumDestaqueAcertoComRagInf` | 64,8% | destaque: Acerto da resposta com RAG (respondíveis): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumDestaqueAcertoComRagSup` | 87,2% | destaque: Acerto da resposta com RAG (respondíveis): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumDestaqueAcertoSemRag` | 0,0% | destaque: Acerto da resposta sem RAG (respondíveis) | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumDestaqueNRespondiveis` | 50 | destaque: Perguntas respondíveis em que o acerto é medido | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, figuras/acerto_por_condicao.png |
| `\NumFiguraCustoRazaoTokens` | 57 | quantas vezes os tokens de entrada médios de uma Condição cabem nos da outra, contexto completo × com RAG, impresso na figura | `scripts/05_figuras.py` | figuras/custo_por_condicao.png |
| `\NumFiguraErrosTotal` | 13 | erros com RAG, somadas todas as Classes de erro, impresso na figura | `scripts/05_figuras.py` | figuras/erros_por_tipo.png |
| `\NumGabaritoNPerguntas` | 60 | Perguntas do Gabarito avaliadas | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, figuras/erros_por_tipo.png, figuras/custo_por_condicao.png |
| `\NumGabaritoNRespondiveis` | 50 | Perguntas respondíveis do Gabarito | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumGabaritoNSemResposta` | 10 | Perguntas sem resposta do Gabarito | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumGabaritoNTipos` | 5 | Tipos de pergunta entre as respondíveis | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumIcNivel` | 95 | nível de confiança dos intervalos de Wilson e de Newcombe, em % | `scripts/04_analisar.py` | README, relatorio/relatorio.tex, figuras/acerto_por_condicao.png |
| `\NumParametrosCommits` | 85d3e4c, fc1a063 e ad0ad19 | commit(s) em que a Rodada principal rodou, na ordem, todos com os mesmos parâmetros congelados | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumParametrosK` | 6 | Trechos recuperados por Pergunta na Condição com RAG (Rodada principal) | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumParametrosModeloEmbeddings` | multilingual-e5-large | modelo de embeddings da busca na Rodada principal, sem o dono do repositório | `scripts/04_analisar.py` | README |
| `\NumParametrosModeloJuiz` | gemini-3.6-flash, gemini-3-flash-preview e gemini-3.1-flash-lite | modelo(s) que julgaram na Rodada principal (a cadeia do Juiz, na ordem de uso) | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumParametrosModeloRespondedor` | gemini-3.5-flash-lite | modelo que responde às Perguntas na Rodada principal | `scripts/04_analisar.py` | README, relatorio/relatorio.tex |
| `\NumParametrosNCommits` | 3 | commits em que a Rodada principal rodou (mais de um: ela foi retomada em outro commit) | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumParametrosNModelosJuiz` | 3 | modelos que julgaram na Rodada principal (mais de um: a cadeia do Juiz, pela cota diária) | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumPrincipalNFallback` | 0 | respostas da Rodada principal dadas por outro modelo (fallback do servidor) | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumPrincipalNRespostas` | 180 | respostas na Rodada principal (Perguntas × Condições) | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumPrincipalTokensEntradaTotal` | 6.067.592 | tokens de entrada na Rodada principal, três Condições | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumPrincipalTokensSaidaTotal` | 133.558 | tokens de saída na Rodada principal, três Condições | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumQuebraAlvo` | 180 | máximo de palavras por Trecho de texto | `scripts/01_extrair.py` | relatorio/relatorio.tex |
| `\NumQuebraSobreposicao` | 30 | máximo de palavras repetidas entre Trechos vizinhos | `scripts/01_extrair.py` | relatorio/relatorio.tex |
| `\NumRepeticoesComparadas` | 2 | repetições da Rodada principal comparadas com ela em ao menos uma Condição completa (Veredictos não revisados) | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumRepeticoesCondicoesIncompletas` | 0 | Condições de repetição que ainda não responderam todas as Perguntas, fora da concordância | `scripts/04_analisar.py` | (não impresso) |
| `\NumRepeticoesIncompletas` | nenhuma | repetições e Condições ainda incompletas, fora da concordância | `scripts/04_analisar.py` | (não impresso) |
| `\NumRepeticoesLeitura` | Para medir isso, a Rodada principal foi repetida, e cada repetição é comparada com ela. | frase do Relatório de avaliação sobre as repetições, escolhida pelas comparadas e incompletas | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumRevisaoVeredictosJuiz` | 42 | Veredictos do Juiz na Rodada principal (três Condições) | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumRevisaoVeredictosMudados` | 0 | Veredictos do Juiz que a Revisão do autor mudou | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumRevisaoVeredictosRevisados` | 42 | Veredictos do Juiz revisados pelo autor | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumRodadasOrigem` | Rodada principal, com os Veredictos do Juiz revisados pelo autor | de onde vêm as Rodadas analisadas, para a capa | `scripts/04_analisar.py` | relatorio/relatorio.tex |
| `\NumSemRagAbstencaoCorreta` | 100,0% | Abstenção correta sem RAG (sem resposta) | `scripts/04_analisar.py` | README, relatorio/tabelas/resultados_por_condicao.tex |
| `\NumSemRagAbstencaoCorretaInf` | 72,2% | Abstenção correta sem RAG (sem resposta): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumSemRagAbstencaoCorretaSup` | 100,0% | Abstenção correta sem RAG (sem resposta): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumSemRagAbstencoesCorretas` | 10 | Abstenções corretas sem RAG (sem resposta) | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagAcertoCitacao` | 0,0% | Acerto da citação sem RAG (respondíveis) | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumSemRagAcertoCitacaoInf` | 0,0% | Acerto da citação sem RAG (respondíveis): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumSemRagAcertoCitacaoSup` | 7,1% | Acerto da citação sem RAG (respondíveis): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex |
| `\NumSemRagAcertoResposta` | 0,0% | Acerto da resposta sem RAG (respondíveis) | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png, figuras/custo_por_condicao.png |
| `\NumSemRagAcertoRespostaInf` | 0,0% | Acerto da resposta sem RAG (respondíveis): limite inferior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png |
| `\NumSemRagAcertoRespostaSup` | 7,1% | Acerto da resposta sem RAG (respondíveis): limite superior do IC de Wilson de 95% | `scripts/04_analisar.py` | relatorio/tabelas/resultados_por_condicao.tex, figuras/acerto_por_condicao.png |
| `\NumSemRagAcertosCitacao` | 0 | acertos da citação sem RAG (respondíveis) | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagAcertosResposta` | 0 | acertos da resposta sem RAG (respondíveis) | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagErrosAbstencaoIndevida` | 50 | Classe de erro 'abstenção indevida' sem RAG (Perguntas) | `scripts/04_analisar.py` | README |
| `\NumSemRagErrosCitacaoErrada` | 0 | Classe de erro 'citação errada' sem RAG (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagErrosFalhaLeitura` | 0 | Classe de erro 'falha de leitura' sem RAG (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagErrosFalhaRecuperacao` | 0 | Classe de erro 'falha de recuperação' sem RAG (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagErrosRespostaInventada` | 0 | Classe de erro 'resposta inventada' sem RAG (Perguntas) | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagLatenciaMedianaS` | 2,7 | latência mediana por Pergunta sem RAG, em segundos | `scripts/04_analisar.py` | relatorio/tabelas/custo_por_condicao.tex, figuras/custo_por_condicao.png |
| `\NumSemRagNFallback` | 0 | respostas sem RAG dadas por outro modelo (fallback do servidor) | `scripts/04_analisar.py` | relatorio/tabelas/custo_por_condicao.tex |
| `\NumSemRagNRespondiveis` | 50 | Perguntas respondíveis na Condição sem RAG | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagNSemResposta` | 10 | Perguntas sem resposta na Condição sem RAG | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagTokensCacheLeituraTotal` | 0 | tokens de entrada lidos do cache sem RAG, soma da Rodada | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagTokensEntradaMedio` | 185 | tokens de entrada sem RAG, média por Pergunta | `scripts/04_analisar.py` | relatorio/tabelas/custo_por_condicao.tex, figuras/custo_por_condicao.png |
| `\NumSemRagTokensEntradaTotal` | 11.099 | tokens de entrada sem RAG, soma da Rodada | `scripts/04_analisar.py` | (não impresso) |
| `\NumSemRagTokensSaidaTotal` | 26.760 | tokens de saída sem RAG, soma da Rodada | `scripts/04_analisar.py` | (não impresso) |

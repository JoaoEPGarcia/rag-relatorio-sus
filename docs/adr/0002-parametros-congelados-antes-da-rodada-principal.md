# Parâmetros congelados antes da Rodada principal

O número de Trechos recuperados, o tamanho do Trecho, o modelo, o esforço e os prompts ficam num arquivo versionado (`parametros.toml`) e são congelados por commit antes da primeira Rodada sobre o Gabarito. Todo ajuste é feito com Perguntas de desenvolvimento, que nunca entram no Gabarito. Ajustar o sistema olhando as 60 Perguntas inflaria a taxa de acerto, porque o sistema estaria sendo ajustado à própria prova. Por isso, quem mudar um parâmetro depois da Rodada principal precisa refazer a Rodada e declarar a mudança.

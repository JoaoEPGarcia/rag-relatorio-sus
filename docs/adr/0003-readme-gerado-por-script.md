# O README é gerado por script, e não editado à mão

O `README.md` é gerado a partir de `README.base.md`, que tem marcadores como `{{acerto_rag}}`, preenchidos com os valores do registro `resultados/numeros.json`. O mesmo registro gera `relatorio/numeros.tex` e `NUMEROS_CANONICOS.md`. A regra do portfólio é que nenhum número impresso seja digitado. Gerar o README é o único jeito de cumprir a regra também no Markdown. Para mudar o texto, edite `README.base.md` e rode `scripts/06_gerar_documentos.py`. O conferidor de números falha se o `README.md` divergir do que o script gera.

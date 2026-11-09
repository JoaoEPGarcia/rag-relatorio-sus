# FAISS com busca exata, e não Chroma

O banco vetorial é o FAISS com índice de busca exata (`IndexFlatIP`), e os metadados de cada Trecho (página, seção) ficam num arquivo ao lado do índice. Com poucas centenas de Trechos, a busca exata custa quase nada e é determinística: a mesma Pergunta recupera sempre os mesmos Trechos. Isso permite testar a busca por TDD com resultados fixos e reproduzir o Acerto da recuperação de uma rodada para outra.

## Opções consideradas

- **Chroma**: guarda os metadados junto com os vetores e tem persistência pronta. Foi rejeitado porque usa busca aproximada (HNSW), que pode variar de resultado, e porque pesa mais na imagem Docker.

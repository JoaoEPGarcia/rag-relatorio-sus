# -*- coding: utf-8 -*-
"""Embeddings dos Trechos e busca vetorial exata.

POR QUE ISTO EXISTE. A Condição com RAG responde a partir dos k Trechos mais
parecidos com a Pergunta. A busca é exata (FAISS IndexFlatIP sobre vetores
normalizados, ou seja, cosseno), e não aproximada, por dois motivos (ADR
0001): com poucas centenas de Trechos ela custa quase nada, e é
determinística: a mesma Pergunta recupera sempre os mesmos Trechos, o que
torna o Acerto da recuperação reprodutível de uma Rodada para outra.

O embutidor é uma interface (`embutir_trechos`, `embutir_pergunta`, `nome`,
`dimensao`), de modo que os testes troquem o modelo de 2,24 GB por um falso.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import faiss
import numpy as np

from rag_sus.modelos import Trecho

MODELO_E5 = "intfloat/multilingual-e5-large"


class Embutidor(Protocol):
    nome: str
    dimensao: int

    def embutir_trechos(self, textos: list[str]) -> np.ndarray: ...

    def embutir_pergunta(self, texto: str) -> np.ndarray: ...


class E5Embutidor:
    """multilingual-e5-large via fastembed (ONNX, sem PyTorch).

    O e5 foi treinado com os prefixos "query: " e "passage: ", e sem eles a
    qualidade da busca cai; o fastembed não os põe sozinho, então pomos aqui.
    """

    nome = MODELO_E5
    dimensao = 1024

    def __init__(self, modelo=None, pasta_cache: str | Path | None = None):
        if modelo is None:
            from fastembed import TextEmbedding

            modelo = TextEmbedding(
                MODELO_E5, cache_dir=str(pasta_cache) if pasta_cache else None
            )
        self._modelo = modelo

    def embutir_trechos(self, textos: list[str]) -> np.ndarray:
        return np.stack(list(self._modelo.embed([f"passage: {t}" for t in textos])))

    def embutir_pergunta(self, texto: str) -> np.ndarray:
        return next(iter(self._modelo.embed([f"query: {texto}"])))


@dataclass(frozen=True)
class Resultado:
    trecho: Trecho
    pontuacao: float


def _normalizar(vetores: np.ndarray) -> np.ndarray:
    vetores = np.asarray(vetores, dtype=np.float32)
    if vetores.ndim == 1:
        vetores = vetores[None, :]
    normas = np.linalg.norm(vetores, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return np.ascontiguousarray(vetores / normas)


class IndiceDeTrechos:
    """Os Trechos e os seus vetores, num índice FAISS de busca exata."""

    def __init__(self, trechos: list[Trecho], indice: faiss.Index, nome_modelo: str):
        if indice.ntotal != len(trechos):
            raise ValueError("índice e lista de Trechos com tamanhos diferentes")
        self.trechos = trechos
        self._indice = indice
        self.nome_modelo = nome_modelo

    @classmethod
    def construir(cls, trechos: list[Trecho], embutidor: Embutidor) -> IndiceDeTrechos:
        if not trechos:
            raise ValueError("não há Trechos para indexar")
        vetores = _normalizar(embutidor.embutir_trechos([t.texto for t in trechos]))
        indice = faiss.IndexFlatIP(vetores.shape[1])
        indice.add(vetores)
        return cls(list(trechos), indice, embutidor.nome)

    def buscar(self, pergunta: str, embutidor: Embutidor, k: int) -> list[Resultado]:
        if embutidor.nome != self.nome_modelo:
            raise ValueError(
                f"índice construído com o modelo {self.nome_modelo}, consulta com {embutidor.nome}"
            )
        k = min(k, len(self.trechos))
        consulta = _normalizar(embutidor.embutir_pergunta(pergunta))
        pontuacoes, posicoes = self._indice.search(consulta, k)
        return [
            Resultado(self.trechos[int(i)], float(p))
            for p, i in zip(pontuacoes[0], posicoes[0], strict=True)
            if i >= 0
        ]

    @staticmethod
    def paginas(resultados: list[Resultado]) -> list[int]:
        """Páginas impressas dos Trechos recuperados, na ordem da busca."""
        return [r.trecho.pagina_impressa for r in resultados]

    # Persistência: o índice vai em bytes (faiss.serialize_index) porque o
    # write_index do FAISS falha com caminhos não ASCII no Windows.

    def salvar(self, pasta: str | Path) -> None:
        pasta = Path(pasta)
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "indice.faiss").write_bytes(faiss.serialize_index(self._indice).tobytes())
        with open(pasta / "trechos.jsonl", "w", encoding="utf-8") as f:
            for t in self.trechos:
                f.write(json.dumps(t.para_dict(), ensure_ascii=False) + "\n")
        meta = {"modelo": self.nome_modelo, "n_trechos": len(self.trechos), "dimensao": self._indice.d}
        (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def carregar(cls, pasta: str | Path, embutidor: Embutidor) -> IndiceDeTrechos:
        pasta = Path(pasta)
        meta = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))
        if meta["modelo"] != embutidor.nome:
            raise ValueError(
                f"índice construído com o modelo {meta['modelo']}, mas o embutidor é {embutidor.nome}"
            )
        dados = np.frombuffer((pasta / "indice.faiss").read_bytes(), dtype=np.uint8)
        indice = faiss.deserialize_index(dados)
        with open(pasta / "trechos.jsonl", encoding="utf-8") as f:
            trechos = [Trecho.de_dict(json.loads(linha)) for linha in f if linha.strip()]
        return cls(trechos, indice, meta["modelo"])

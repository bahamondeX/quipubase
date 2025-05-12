import typing as tp
from collections import defaultdict
from functools import lru_cache

import faiss
import numpy as np
import typing_extensions as tpx
from light_embed import TextEmbedding
from numpy.typing import NDArray

Texts: tpx.TypeAlias = tp.Union[str, list[str]]
EmbeddingModel: tpx.TypeAlias = tp.Literal["poly-sage", "deep-pulse", "mini-scope"]

MODELS: dict[EmbeddingModel, TextEmbedding] = {
    "poly-sage": TextEmbedding("nomic-ai/nomic-embed-text-v1.5"),
    "deep-pulse": TextEmbedding("sentence-transformers/all-mpnet-base-v2"),
    "mini-scope": TextEmbedding("sentence-transformers/all-MiniLM-L6-v2"),
}


class EmbeddingService(tp.NamedTuple):
    model: EmbeddingModel

    def encode(self, data: Texts) -> NDArray[np.float32]:
        if isinstance(data, str):
            data = [data]
        return MODELS[self.model].encode(data).astype(np.float32)

    def search(
        self, query: str, corpus: list[str], top_k: int = 3
    ) -> list[tuple[str, float]]:
        corpus_embeddings = self.encode(corpus)
        dim = corpus_embeddings.shape[1]

        index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(corpus_embeddings)
        index.add(corpus_embeddings)

        query_embedding = self.encode(query)[0].reshape(1, -1)
        faiss.normalize_L2(query_embedding)

        scores, indices = index.search(query_embedding, top_k)
        return [(corpus[i], float(scores[0][j])) for j, i in enumerate(indices[0])]

    def cluster(self, corpus: list[str], n: int) -> dict[str, list[str]]:
        assert n < len(corpus) // 2, "n must be less than half the number of texts"

        embeddings = self.encode(corpus)
        faiss.normalize_L2(embeddings)
        dim = embeddings.shape[1]

        # 1. KMeans clustering
        kmeans = faiss.Kmeans(
            d=dim, k=n, niter=50, verbose=False, min_points_per_centroid=1
        )
        kmeans.train(embeddings)
        _, labels = kmeans.index.search(embeddings, 1)
        labels = labels.flatten()

        # 2. Agrupar textos y embeddings por cluster
        cluster_texts = defaultdict(list)
        cluster_embeds = defaultdict(list)
        for text, label, emb in zip(corpus, labels, embeddings):
            cluster_texts[label].append(text)
            cluster_embeds[label].append(emb)

        # 3. Centroides de cada cluster
        centroids = {i: np.mean(np.vstack(cluster_embeds[i]), axis=0) for i in range(n)}

        # 4. Encontrar la key de cada cluster
        result: dict[str, list[str]] = {}
        for i in range(n):
            others = [centroids[j] for j in range(n) if j != i]
            target = np.mean(np.vstack(others), axis=0)
            best_text, best_score = None, -np.inf
            for text, emb in zip(cluster_texts[i], cluster_embeds[i]):
                score = np.dot(emb, target)
                if score > best_score:
                    best_text = text
                    best_score = score
            result[best_text] = cluster_texts[i]

        return result

import typing as tp
from collections import defaultdict

import faiss  # type: ignore
import numpy as np
import typing_extensions as tpx
from light_embed import TextEmbedding  # type: ignore
from numpy.typing import NDArray

Texts: tpx.TypeAlias = tp.Union[str, list[str]]
EmbeddingModel: tpx.TypeAlias = tp.Literal["poly-sage", "deep-pulse", "mini-scope"]
Semantic: tpx.TypeAlias = tp.Union[Texts, NDArray[np.float32]]

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
        return MODELS[self.model].encode(data).astype(np.float32)  # type: ignore

    def search(
        self, query: str, corpus: Semantic, top_k: int = 3
    ) -> list[tuple[str, float]]:
        if isinstance(corpus, list):
            corpus = self.encode(corpus)
        dim = corpus.shape[1]  # type: ignore

        index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(corpus) # type: ignore
        index.add(corpus) # type: ignore

        query_embedding = self.encode(query)[0].reshape(1, -1) # type: ignore
        faiss.normalize_L2(query_embedding)  # type: ignore

        scores, indices = index.search(query_embedding, # type: ignore
        top_k) # type: ignore
        return [(corpus[i], float(scores[0][j])) for j, i in enumerate(indices[0])]  # type: ignore

    def cluster(self, corpus: Semantic, n: int) -> dict[str, list[str]]:
        if isinstance(corpus, list):
            corpus = self.encode(corpus)
        assert n < len(corpus) // 2, "n must be less than half the number of texts"
        faiss.normalize_L2(corpus)  # type: ignore
        dim = corpus.shape[1]  # type: ignore

        # 1. KMeans clustering
        kmeans = faiss.Kmeans(
            d=dim, # type: ignore
            k=n,  # type: ignore
            niter=50,
            verbose=False,
            min_points_per_centroid=1,
        )
        kmeans.train(corpus)  # type: ignore
        _, labels = kmeans.index.search(corpus, 1)  # type: ignore
        labels = labels.flatten()  # type: ignore

        # 2. Agrupar textos y embeddings por cluster
        cluster_texts = defaultdict[list[str]](list)  # type: ignore
        cluster_embeds = defaultdict[list[NDArray[np.float32]]](list)  # type: ignore
        for text, label, emb in zip(corpus, labels, corpus):  # type: ignore
            cluster_texts[label].append(text)  # type: ignore
            cluster_embeds[label].append(emb)  # type: ignore

        # 3. Centroides de cada cluster
        centroids = {
            i: np.mean(np.vstack(cluster_embeds[i]), axis=0)  # type: ignore
            for i in range(n)
        }

        # 4. Encontrar la key de cada cluster
        result: dict[str, list[str]] = {}
        for i in range(n):
            others = [centroids[j] for j in range(n) if j != i]
            target = np.mean(np.vstack(others), axis=0)
            best_text, best_score = None, -np.inf
            for text, emb in zip( # type: ignore
                cluster_texts[i], cluster_embeds[i]  # type: ignore
            ):  # type: ignore
                score = np.dot(emb, target)  # type: ignore
                if score > best_score:
                    best_text = text  # type: ignore
                    best_score = score
            result[best_text] = cluster_texts[i]  # type: ignore

        return result

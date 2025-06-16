import time

import numpy as np
from fastapi import APIRouter

from quipubase.lib.exceptions import QuipubaseException

from .services import VectorStoreService
from .typedefs import (DeleteResponse, DeleteText, Embedding, EmbedResponse,
                       EmbedText, QueryResponse, QueryText, UpsertResponse)


def route() -> APIRouter:
    app = APIRouter(tags=["vector"])

    @app.get("/vector/{namespace}/{id}")
    def _(namespace: str, id: str):
        return Embedding.retrieve(namespace=namespace, id=id)

    @app.post("/vector/{namespace}", response_model=UpsertResponse)
    def _(namespace: str, data: EmbedText):
        """
        Upsert texts into the vector store.

        Args:
                namespace: The namespace to store the embeddings in
                texts: List of texts to embed and store
                model: The embedding model to use

        Returns:
                UpsertResponse containing the IDs of the upserted embeddings and count
        """
        try:
            store = VectorStoreService(namespace=namespace, model=data.model)
            embeddings = [
                Embedding(content=data.input, embedding=store.embed(data.input))
                
            ]
            response = store.upsert(embeddings)
            return response
        except Exception as e:
            raise QuipubaseException(status_code=500, detail=str(e))

    @app.put("/{namespace}", response_model=QueryResponse)
    def _(namespace: str, data: QueryText):
        """
        Query the vector store for similar texts.

        Args:
                namespace: The namespace to query
                query: The text query to search for similar content
                top_k: Number of results to return
                model: The embedding model to use

        Returns:
                QueryResponse containing the matched texts and their similarity scores
        """
        try:
            store = VectorStoreService(namespace=namespace, model=data.model)
            return store.query(store.embed(data.input).tolist(), data.top_k)
        except Exception as e:
            raise QuipubaseException(status_code=500, detail=str(e))

    @app.delete("/vector/{namespace}", response_model=DeleteResponse)
    def _(
        namespace: str,
        data: DeleteText,
    ):
        """
        Delete embeddings from the vector store.

        Args:
                namespace: The namespace to delete embeddings from
                ids: List of IDs to delete

        Returns:
                DeleteResponse containing the IDs of the deleted embeddings and count
        """
        try:
            store = VectorStoreService(namespace=namespace, model="mini-scope")
            response = store.delete(ids=data.ids)
            return response
        except Exception as e:
            raise QuipubaseException(status_code=500, detail=str(e))

    @app.post("/embeddings", response_model=EmbedResponse)
    def _(data: EmbedText):
        start = time.perf_counter()
        vs = VectorStoreService(namespace="quipubase", model=data.model)
        embeddings: list[list[float]] = vs.embed(data.input).tolist()
        end = time.perf_counter()
        return EmbedResponse(
            data=[
                Embedding(content=c, embedding=np.array(e).astype(np.float32))
                for c, e in zip(data.input, embeddings)
            ],
            ellapsed=end - start,
            count=len(embeddings),
        )

    return app

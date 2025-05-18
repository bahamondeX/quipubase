import time
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..store import (DeleteResponse, Embedding, EmbeddingModel, QueryResponse,
                     UpsertResponse, VectorStore)


class EmbedText(BaseModel):
    content: list[str]
    model: EmbeddingModel


class UpsertText(EmbedText):
    namespace: str


class QueryText(EmbedText):
    namespace: str
    top_k: int


class DeleteText(BaseModel):
    namespace: str
    ids: list[str]


def store_router() -> APIRouter:
    app = APIRouter(tags=["stores"], prefix="/vector")

    @app.post("/upsert", response_model=UpsertResponse)
    async def _(data: UpsertText):
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
            store = VectorStore(namespace=data.namespace, model=data.model)
            embeddings = [
                Embedding(content=text, embedding=store.embed(text))
                for text in data.content
            ]
            response = store.upsert(embeddings)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/query", response_model=QueryResponse)
    async def _(data: QueryText):
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
            store = VectorStore(namespace=data.namespace, model=data.model)
            return store.query(store.embed(data.content).tolist(), data.top_k)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/delete", response_model=DeleteResponse)
    async def _(
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
            store = VectorStore(namespace=data.namespace, model="mini-scope")
            response = store.delete(ids=data.ids)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/embed")
    async def _(data: EmbedText):
        start = time.perf_counter()
        vs = VectorStore(namespace="default", model=data.model)
        embeddings: list[list[float]] = vs.embed(data.content).tolist()
        end = time.perf_counter()
        return {
            "data": [
                Embedding(content=c, embedding=np.array(e).astype(np.float32))
                for c, e in zip(data.content, embeddings)
            ],
            "created": end - start,
            "embedCount": len(embeddings),
        }

    return app

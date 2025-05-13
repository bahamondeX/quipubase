from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..store import (DeleteResponse, Embedding, EmbeddingModel, QueryResponse,
                     UpsertResponse, VectorStore)


class UpsertText(BaseModel):
    content: list[str]
    namespace: str
    model: EmbeddingModel


class QueryText(BaseModel):
    query: str
    namespace: str
    top_k: int
    model: EmbeddingModel


class DeleteText(BaseModel):
    namespace: str
    ids: list[str]


def store_router() -> APIRouter:
    app = APIRouter(tags=["stores"])

    @app.put("/embeddings", response_model=UpsertResponse)
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

    @app.post("/embeddings", response_model=QueryResponse)
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
            return store.query(store.embed(data.query), data.top_k)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/embeddings", response_model=DeleteResponse)
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

    return app

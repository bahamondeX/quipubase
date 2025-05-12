from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .data import Collection
from .models import CollectionType, JsonSchemaModel, QuipubaseRequest
from .routes import collections_router, pubsub_router

# Import all necessary components to avoid forward reference issues

# Rebuild models after all imports are resolved to avoid forward reference issues

__all__ = ["CollectionType", "Collection", "create_app"]


def model_rebuild():
    for model in BaseModel.__subclasses__():
        model.model_rebuild()
    Collection.model_rebuild()
    QuipubaseRequest.model_rebuild()
    JsonSchemaModel.model_rebuild()


def create_app():
    model_rebuild()
    static_files = StaticFiles(directory="web/dist", html=True)
    app = FastAPI(
        title="Quipubase",
        description="**Quipubase** is a **real-time document database** designed for _AI-native_ applications. Built on top of `RocksDB`, it enables **dynamic, schema-driven collections** using `jsonschema` for flexible document modeling. With **native support for vector similarity search**, Quipubase empowers intelligent querying at scale. Its built-in `pub/sub` architecture allows **real-time subscriptions to document-level events**, making it _a powerful backend for live, reactive AI systems_.",
        version="0.0.1",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(collections_router(), prefix="/v1")
    app.include_router(pubsub_router(), prefix="/v1")
    app.mount("/", static_files, name="static")

    return app

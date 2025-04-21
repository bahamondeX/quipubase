from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .collection import Collection
from .typedefs import CollectionType, JsonSchemaModel

# Import all necessary components to avoid forward reference issues

# Rebuild models after all imports are resolved to avoid forward reference issues

__all__ = ["CollectionType", "Collection", "create_app"]


def create_app():
    # Import handlers here to avoid circular imports
    from pydantic import BaseModel

    from .handlers import collections_router, pubsub_router
    from .handlers.collections import ActionRequest

    # Rebuild all models to resolve forward references
    for model in BaseModel.__subclasses__():
        model.model_rebuild()
    Collection.model_rebuild()
    CollectionType.model_rebuild()
    ActionRequest.model_rebuild()
    JsonSchemaModel.model_rebuild()
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
    return app

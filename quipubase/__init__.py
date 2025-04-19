from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .collection import Collection
from .typedefs import CollectionType, JsonSchemaModel

# Import all necessary components to avoid forward reference issues

# Rebuild models after all imports are resolved to avoid forward reference issues

__all__ = ["CollectionType", "Collection", "create_app"]


def create_app():
    # Import handlers here to avoid circular imports
    from .handlers import collections_router, pubsub_router
    from .handlers.collections import ActionRequest
    from .handlers.pubsub import PubActionResponse
    from pydantic import BaseModel

    # Rebuild all models to resolve forward references
    for model in BaseModel.__subclasses__():
        model.model_rebuild()
    Collection.model_rebuild()
    CollectionType.model_rebuild()
    ActionRequest.model_rebuild()
    PubActionResponse.model_rebuild()
    JsonSchemaModel.model_rebuild()
    app = FastAPI()
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

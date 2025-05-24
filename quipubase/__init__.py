from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from .collections import Collection, CollectionType, JsonSchemaModel, QuipubaseRequest
from .auth import route as auth_router
from .events import route as pubsub_router
from .files import route as content_router
from .collections import route as data_router
from .vector import route as setup_routes

__all__ = [
    "data_router",
    "pubsub_router",
    "setup_routes",
    "auth_router",
    "content_router",
]


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
    app.include_router(data_router(), prefix="/v1")
    app.include_router(pubsub_router(), prefix="/v1")
    app.include_router(setup_routes(), prefix="/v1")
    app.include_router(auth_router(), prefix="/v1")
    app.include_router(content_router(), prefix="/v1")

    @app.get("/", include_in_schema=False)
    def _():
        return HTMLResponse(Path("index.html").read_text())

    @app.get("/favicon.svg", include_in_schema=False)
    def _():
        return FileResponse("./favicon.svg")

    return app

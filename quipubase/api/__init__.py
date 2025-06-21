from fastapi import FastAPI
from pydantic import BaseModel

from ..lib import setup
from .audio import route as audio_routes
from .auth import route as auth_routes
from .chat import route as chat_routes
from .collections import Collection, JsonSchemaModel, QuipubaseRequest
from .collections import route as collections_routes
from .collections.objects import route as objects_routes
from .files import route as files_routes
from .images import route as images_routes
from .models import route as models_routes
from .music import route as music_routes
from .vector import route as vector_routes


def model_rebuild():
    for model in BaseModel.__subclasses__():
        model.model_rebuild()
    Collection.model_rebuild()
    QuipubaseRequest.model_rebuild()
    JsonSchemaModel.model_rebuild()


@setup
def create_app():
    model_rebuild()
    app = FastAPI(
        debug=True,
        title="Quipubase",
        description="""**Quipubase** is a cutting-edge, **real-time document database** specifically engineered for the demands of **AI-native applications**.
        **Key Features for Developers:**
        * **High Performance:** Built on `RocksDB` for efficient, high-throughput data operations.
        * **Flexible Schemas:** Define dynamic, self-validating collections using `jsonschema`, adapting effortlessly to evolving data models.
        * **Integrated Vector Search:** Leverage native support for **vector similarity search** to power intelligent querying, recommendations, and semantic search capabilities at scale.
        * **Real-time Reactivity:** Implement live, reactive AI systems with a robust `pub/sub` architecture, providing **real-time subscriptions to document-level events**.
        * **Simplified Development:** Designed to be the ideal backend for modern, intelligent applications, streamlining data management for AI workflows.
        Quipubase empowers developers to build responsive, intelligent, and scalable AI-driven solutions with ease.
        """,
        version="0.0.1",
    )
    for r in (
        audio_routes,
        auth_routes,
        collections_routes,
        chat_routes,
        objects_routes,
        audio_routes,
        images_routes,
        files_routes,
        models_routes,
        vector_routes,
        music_routes,
    ):
        app.include_router(r(), prefix="/v1")
    return app

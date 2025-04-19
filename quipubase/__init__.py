from .collection import Collection
from .typedefs import CollectionType
from .api import QuipuBase

# Rebuild models after all imports are resolved to avoid forward reference issues
Collection.model_rebuild()
CollectionType.model_rebuild()

__all__ = ["QuipuBase", "Collection"]


def create_app():
    return QuipuBase()

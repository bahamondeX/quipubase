import typing as tp

from pydantic import BaseModel

from ..models.typedefs import QuipuActions
from .collection import Collection

T = tp.TypeVar("T", bound=Collection, covariant=True)


class EventType(BaseModel, tp.Generic[T]):
    """Event model"""

    event: QuipuActions
    data: T | None

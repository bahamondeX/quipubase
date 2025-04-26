import typing as tp

from pydantic import BaseModel

from .collection import Collection
from ..models.typedefs import QuipuActions

T = tp.TypeVar("T", bound=Collection, covariant=True)


class Event(BaseModel, tp.Generic[T]):
    """Event model"""

    event: QuipuActions
    data: T | None

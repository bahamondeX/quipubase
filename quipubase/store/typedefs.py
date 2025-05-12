import typing as tp
from uuid import UUID

import numpy as np
import typing_extensions as tpe
from numpy.typing import NDArray

MetaData: tpe.TypeAlias = tp.Dict[str, tp.Union[str, int, float, bool, None, list[str]]]


class Embedding(tpe.TypedDict):
    id: UUID
    embedding: NDArray[np.float32]
    metadata: MetaData


class EmbeddingUpsertResponse(tpe.TypedDict):
    upsertedCount: int


class QueryMatch(tpe.TypedDict):
    id: UUID
    score: float
    metadata: MetaData


class QueryResponse(tpe.TypedDict):
    matches: list[QueryMatch]

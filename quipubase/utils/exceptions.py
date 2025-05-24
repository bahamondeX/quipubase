import json
from dataclasses import asdict, dataclass, field

@dataclass
class QuipubaseException(BaseException):
    """Base Tool Exception for handling errors on multiple backends"""

    detail: str
    status_code: int = field(default=500)

    def model_dump(self):
        return asdict(self)

    def model_dump_json(self):
        return json.dumps(asdict(self))

    def dict(self):
        return asdict(self)

    def json(self):
        return json.dumps(asdict(self))

    def __str__(self):
        return self.json()

    def __repr__(self):
        return self.__str__()
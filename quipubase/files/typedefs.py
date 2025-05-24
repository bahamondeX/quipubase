from pydantic import BaseModel


class ContentResponse(BaseModel):
    chunks: list[str]
    created: float
    chunkedCount: int

class UploadedFile(BaseModel):
    url: str
    created: float
    key: str
    size: int | None = None
    content_type: str | None = None
    

class GetFile(BaseModel):
    url: str
    created: float
    key: str
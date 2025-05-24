import typing as tp
from fastapi import APIRouter, File, UploadFile, Query
from sse_starlette import EventSourceResponse

from .typedefs import ChunkFile, GetOrCreateFile
from .service import ContentService, GCS_BUCKET

cs = ContentService()


def route():
    content = APIRouter(tags=["files"], prefix="/files")

    @content.post("", response_model=ChunkFile)
    async def _(format: tp.Literal["html", "text"], file: UploadFile = File(...)):
        return await cs.run(file, format)  # type: ignore
    
    @content.put("", response_model=GetOrCreateFile)
    async def _(file: UploadFile = File(...), bucket: tp.Optional[str] = Query(default=None)):
        if bucket:
            return await cs.put(file, bucket)
        return await cs.put(file)
    
    @content.get("/{key}", response_model=GetOrCreateFile)
    def _(key: str, bucket: tp.Optional[str] = Query(default=None)):
        if bucket:
            return cs.get(key, bucket)
        return cs.get(key)
        
    @content.delete("/{key}", response_model=dict[str, bool])
    def _(key: str):
        return cs.delete(key)
    
    @content.get("/tree/{default}", response_class=EventSourceResponse)
    def _(prefix:str=Query(default=""),bucket:str = Query(default=GCS_BUCKET)):
        prefix = prefix or ""
        def event() -> tp.Generator[str, None, None]:
            for chunk in cs.scan(prefix,bucket):
                yield chunk.model_dump_json()
        return EventSourceResponse(event())
    
    return content
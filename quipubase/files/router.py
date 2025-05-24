import typing as tp
from fastapi import APIRouter, File, Path, UploadFile, Query
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
    async def _(path:str,file: UploadFile = File(...), bucket: tp.Optional[str] = Query(default=None)):
        if bucket:
            return await cs.put(path,file, bucket)
        return await cs.put(path,file)
    
    @content.get("/{path}", response_model=GetOrCreateFile)
    def _(path: str, bucket: tp.Optional[str] = Query(default=None)):
        if bucket:
            return cs.get(path, bucket)
        return cs.get(path)
        
    @content.delete("/{path}", response_model=dict[str, bool])
    def _(path: str, bucket:tp.Optional[str]=Query(default=None)):
        if bucket:
            return cs.delete(path,bucket)
        return cs.delete(path)
    
    @content.get("/tree/{prefix}", response_class=EventSourceResponse)
    def _(prefix:str=Path(...),bucket:str = Query(default=GCS_BUCKET)):
        prefix = prefix or ""
        def event() -> tp.Generator[str, None, None]:
            for chunk in cs.scan(prefix,bucket):
                yield chunk.model_dump_json()
        return EventSourceResponse(event())
    
    return content
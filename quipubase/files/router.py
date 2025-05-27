import typing as tp
from fastapi import APIRouter, File, Path, UploadFile, Query
from sse_starlette import EventSourceResponse

from quipubase.utils.utils import handle

from .typedefs import ChunkFile, GetOrCreateFile
from .service import ContentService

cs = ContentService()


def route():
    content = APIRouter(tags=["files"])

    @content.post("/files", response_model=ChunkFile)
    async def _(format: tp.Literal["html", "text"], file: UploadFile = File(...)):
        return await cs.run(file, format)  # type: ignore
    
    @content.put("/files/{path:path}", response_model=GetOrCreateFile)
    async def _(path:str,file: UploadFile = File(...), bucket: tp.Optional[str] = Query(default=None)):
        if bucket:
            return await cs.put(path,file, bucket)
        return await cs.put(path,file)

    @content.get("/file/{path:path}", response_model=GetOrCreateFile)
    @handle
    def _(path: str = Path(...), bucket: tp.Optional[str] = Query(default=None)):
        if bucket:
            return cs.get(path, bucket)
        return cs.get(path)

    @content.delete("/files/{path:path}", response_model=dict[str, bool])
    @handle
    def _(path: str = Path(...), bucket:tp.Optional[str]=Query(default=None)):
        if bucket:
            return cs.delete(path,bucket)
        return cs.delete(path)

    @content.get("/filestree/{path:path}", response_model=GetOrCreateFile)
    def _(path: str = Path(...), bucket: tp.Optional[str] = Query(default=None)):
        return EventSourceResponse(cs.scan(path, bucket) if bucket else cs.scan(path))
        # type: ignore
    return content


import typing as tp

from fastapi import APIRouter, File, UploadFile

from .typedefs import ContentResponse, ContentService, UploadedFile, GetFile

cs = ContentService()


def route():
    content = APIRouter(tags=["files"], prefix="/files")

    @content.post("", response_model=ContentResponse)
    async def _(format: tp.Literal["html", "text"], file: UploadFile = File(...)):
        return await cs.run(file, format)  # type: ignore

    return content

    @content.put("/upload", response_model=UploadedFile)
    async def _(file: UploadFile = File(...)):
        return await cs.put(file)  # type: ignore
    
    @content.get("", response_model=GetFile)
    async def _(key: str):
        return cs.get(key)  # type: ignore
    
    @content.delete("")
    async def _(key: str):
        return cs.delete(key)  # type: ignore
    
    return content
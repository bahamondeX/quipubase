import typing as tp
from fastapi import APIRouter, UploadFile, File
from ..content import ContentService, ContentResponse

cs = ContentService()

def content_router():
	content = APIRouter(tags=["file"],prefix="/file")
	@content.post("",response_model=ContentResponse)
	async def _(format:tp.Literal["html","text"],file:UploadFile=File(...)):
		return await cs.run(file,format) # type: ignore
	return content


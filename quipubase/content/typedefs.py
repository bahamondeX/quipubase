from pydantic import BaseModel

class ContentResponse(BaseModel):
	chunks:list[str]
	created:float
	chunkedCount:int
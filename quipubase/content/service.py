import time
import typing as tp
from ..docs import load_document
from fastapi import UploadFile
from .typedefs import ContentResponse

class ContentService:
	async def run(self,file:UploadFile, format:tp.Literal["html","text"]):
		start = time.perf_counter()
		def generator():
			pivot = ""
			for chunk in load_document(file,format=='text'):
				if chunk == pivot or len(chunk) == 0:
					continue
				pivot = chunk
				yield chunk
		
		chunks = list(generator())
		chunkedCount = len(chunks)
		created = time.perf_counter()-start
		return ContentResponse(chunks=chunks,created=created,chunkedCount=chunkedCount)
	
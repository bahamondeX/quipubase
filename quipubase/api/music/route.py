from fastapi import APIRouter
from .typedefs import MusicGenerationParams
from .service import MusicGenerationService
from fastapi.responses import StreamingResponse
service = MusicGenerationService()

def route():
	app = APIRouter(tags=["music"],prefix="/music/generations")
	@app.post("")
	async def _(request:MusicGenerationParams):
		return StreamingResponse(service.run(data=request))
	return app
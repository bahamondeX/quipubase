from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from .service import MusicGenerationService
from .typedefs import MusicGenerationParams

service = MusicGenerationService()


def route():
    app = APIRouter(tags=["music"], prefix="/music/generations")

    @app.post("")
    async def _(request: MusicGenerationParams):
        return StreamingResponse(service.run(data=request))

    return app

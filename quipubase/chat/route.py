from fastapi import APIRouter, Body
from sse_starlette import EventSourceResponse
from .service import LLMRun

app = APIRouter(prefix="/chat")


def route():
    @app.post("/completions")
    async def _(
        agent: LLMRun = Body(...),
    ):
        
        return EventSourceResponse(agent.run())
    
    return app


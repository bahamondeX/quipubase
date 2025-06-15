from fastapi import APIRouter, Body
from sse_starlette import EventSourceResponse

from .service import DeepResearch

app = APIRouter(prefix="/chat", tags=["chat"])


def route():
    @app.post("/completions")
    async def _(
        agent: DeepResearch = Body(...),
    ):
        async def generator():
            async for chunk in agent.run():
                yield chunk.model_dump_json()

        return EventSourceResponse(generator())

    return app

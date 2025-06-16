from fastapi import APIRouter, Body
from sse_starlette import EventSourceResponse
from openai.types.chat.chat_completion import ChatCompletion as OpenAIChatCompletion

from .service import ChatCompletion

app = APIRouter(prefix="/chat", tags=["chat"])


def route():
    @app.post("/completions")
    async def _(
        agent: ChatCompletion = Body(...),
    ):
        response = await agent.run()
        if not isinstance(response, OpenAIChatCompletion):
            async def generator():
                async for chunk in response:
                    yield chunk.model_dump_json()
            return EventSourceResponse(generator())
        return response
    
    return app

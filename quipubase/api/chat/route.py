

from fastapi import APIRouter, Body
from openai.types.chat.chat_completion import \
    ChatCompletion as OpenAIChatCompletion
from sse_starlette import EventSourceResponse

from .service import ChatCompletion

app = APIRouter(prefix="/chat", tags=["chat"])


def route():
    @app.post("/completions")
    async def _(
        agent: ChatCompletion = Body(...),
    ):
        response = await agent.run()
        if isinstance(response, OpenAIChatCompletion):
            return response
        else:

            async def generator():
                async for chunk in response:
                    yield chunk.model_dump_json(exclude_none=True)

            return EventSourceResponse(generator())

    return app

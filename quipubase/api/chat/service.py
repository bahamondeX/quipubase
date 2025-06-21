import json
import os
import time
import typing as tp
import uuid
from abc import ABC, abstractmethod

import httpx
from groq import AsyncGroq
from groq.types.chat.chat_completion_message_param import \
    ChatCompletionMessageParam
from groq.types.chat.chat_completion_tool_choice_option_param import \
    ChatCompletionToolChoiceOptionParam
from groq.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai import AsyncOpenAI
from openai._utils._proxy import LazyProxy
from openai.types.chat.chat_completion import \
    ChatCompletion as OpenAIChatCompletion
from openai.types.chat.chat_completion_chunk import (ChatCompletionChunk,
                                                     Choice, ChoiceDelta)
from pydantic import BaseModel, Field

T = tp.TypeVar("T")

client = AsyncGroq()

MAPPING: dict[str, str] = {
    "llama-3.3-70b-versatile": "versatile",
    "llama-3.1-8b-instant": "instant",
    "meta-llama/llama-4-scout-17b-16e-instruct": "scout",
    "meta-llama/llama-4-maverick-17b-128e-instruct": "maverick",
}

REVERSE_MAPPING: dict[str, str] = {v: k for k, v in MAPPING.items()}


class Tool(BaseModel, LazyProxy[T], ABC):
    model_config = {"extra": "ignore"}

    @classmethod
    def tool_definition(cls) -> ChatCompletionToolParam:
        return ChatCompletionToolParam(
            type="function",
            function={
                "name": cls.__name__,
                "description": cls.__doc__ or "",
                "parameters": cls.model_json_schema().get("properties", {}),
            },
        )

    @abstractmethod
    def run(self) -> tp.AsyncGenerator[ChatCompletionChunk, tp.Any]:
        raise NotImplementedError

    @abstractmethod
    def __load__(self) -> T:
        raise NotImplementedError

    def _parse_chunk(self, chunk: str):
        return ChatCompletionChunk(
            id=str(uuid.uuid4()),
            choices=[Choice(delta=ChoiceDelta(content=chunk), index=0)],
            created=int(time.time()),
            model="",
            object="chat.completion.chunk",
        )


class OpenAITool(Tool[AsyncOpenAI]):
    model_config = {"extra": "allow"}

    @abstractmethod
    def run(self) -> tp.AsyncGenerator[ChatCompletionChunk, tp.Any]:
        raise NotImplementedError

    def __load__(self):
        return AsyncOpenAI()


class Transcribe(Tool[AsyncOpenAI]):
    model_config = {"extra": "allow"}
    url: str = Field(..., description="Url of the audio file to transcribe")

    def __load__(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    async def run(self):
        client = self.__load__()
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(self.url, headers={"Accept": "audio/wav"})
            async for chunk in response.aiter_bytes(1024 * 1024):
                transcription = await client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo", file=chunk
                )
                yield self._parse_chunk(transcription.text)


class GoogleSearch(OpenAITool):
    model_config = {"extra": "allow"}
    q: str = Field(..., description="The query to search for.")

    async def run(self) -> tp.AsyncGenerator[ChatCompletionChunk, tp.Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/customsearch/v1?key={os.getenv('SEARCH_ENGINE_API_KEY')}&cx={os.getenv('SEARCH_ENGINE_ID')}&q={self.q}"
            )
            response_json = response.json()
            yield self._parse_chunk(json.dumps(response_json))


class ChatCompletion(BaseModel):
    model_config = {"extra": "ignore"}
    model: str = Field(
        default="maverick", description="The model to use for the chat completion."
    )
    messages: tp.List[ChatCompletionMessageParam] = Field(
        ..., description="The messages to guide the deep research process."
    )
    tools: tp.Optional[tp.List[ChatCompletionToolParam]] = Field(
        default=None,
        description="The tools that the model can utilize during the research.",
    )
    tool_choice: ChatCompletionToolChoiceOptionParam = Field(default="auto")
    stream: bool = Field(default=True)
    max_completion_tokens: int = Field(
        default=8192,
        description="The maximum number of tokens to generate in the research run.",
    )
    max_tokens: tp.Optional[int] = Field(default=None)

    async def run(
        self,
    ) -> tp.Union[OpenAIChatCompletion, tp.AsyncGenerator[ChatCompletionChunk, None]]:
        model_id = REVERSE_MAPPING.get(self.model, self.model)
        payload = self.model_dump(exclude_none=True)
        payload["model"] = model_id

        return await client.chat.completions.create(**payload)  # type: ignore

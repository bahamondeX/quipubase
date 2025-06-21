import typing as tp

from openai import AsyncOpenAI
from openai.types.chat.chat_completion import \
    ChatCompletion as OpenAIChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import \
    ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_choice_option_param import \
    ChatCompletionToolChoiceOptionParam
from openai.types.chat.chat_completion_tool_param import \
    ChatCompletionToolParam
from pydantic import BaseModel, Field

T = tp.TypeVar("T")

client = AsyncOpenAI()


class ChatCompletion(BaseModel):
    model_config = {"extra": "ignore"}
    model: str = Field(
        default="gemini-flash-2.5",
        description="The model to use for the chat completion.",
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
        payload = self.model_dump(exclude_none=True)
        return await client.chat.completions.create(**payload)  # type: ignore

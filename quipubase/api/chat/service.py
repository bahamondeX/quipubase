import json
import os
import time
import typing as tp
import uuid
from abc import ABC, abstractmethod

import httpx
from openai import AsyncOpenAI
from openai._utils._proxy import LazyProxy
from openai.types.chat.chat_completion_chunk import (ChatCompletionChunk,
                                                     Choice, ChoiceDelta)
from openai.types.chat.chat_completion_message_param import \
    ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_choice_option_param import \
    ChatCompletionToolChoiceOptionParam
from openai.types.chat.chat_completion_tool_param import \
    ChatCompletionToolParam
from pydantic import BaseModel, Field

T = tp.TypeVar("T")


class Tool(BaseModel, LazyProxy[T], ABC):
    """Base Tool class for all vendors tool framework implementations"""

    model_config = {"extra": "allow"}

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
    """
    Base class for tools that interact with OpenAI-compatible APIs.
    Subclasses should implement the `run` method to define the tool's functionality.
    """

    model_config = {"extra": "allow"}

    @abstractmethod
    def run(self) -> tp.AsyncGenerator[ChatCompletionChunk, tp.Any]:
        raise NotImplementedError

    def __load__(self):
        return AsyncOpenAI()


class Transcribe(Tool[AsyncOpenAI]):
    """
    Transcribe Tool
    ------------
    **Description**: This tool transcribes an audio file from a given URL. It fetches the audio file and then uses a transcription service to convert the audio into text.

    **Input**:
    - `url`: The URL of the audio file to transcribe (string, required). Ensure the URL is publicly accessible and the file is in a supported audio format.

    **Output**:
    - A stream of text chunks representing the transcription of the audio file. Each chunk is part of a `ChatCompletionChunkTypedDict`.

    **Vendor**: Uses the Groq OpenAI API endpoint for transcription.
    **Model**: `whisper-large-v3-turbo`

    **Example Usage**:
    ```json
    {
      "url": "[https://example.com/audio.wav](https://example.com/audio.wav)"
    }
    ```
    """

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
    """
    GoogleSearch
    ------------
    **Description**: This tool performs a Google Custom Search to retrieve relevant web results based on a given query. Use this tool when the information needed to answer a user's question might not be in your training data or falls after your knowledge cut-off date.

    **Input**:
    - `q`: The query to search for (string, required). This should be a concise and effective search query to get the best results.

    **Output**:
    - A JSON string containing the search results from Google. The structure of this JSON object follows the Google Custom Search API response format. Each chunk is part of a `ChatCompletionChunkTypedDict`.

    **Constraints**:
    - Ensure that the environment variables `SEARCH_ENGINE_API_KEY` and `SEARCH_ENGINE_ID` are properly configured for this tool to function.
    - **Cut-off date**: `2025 May 05`

    **Example Usage**:
    ```json
    {
      "q": "latest advancements in AI research"
    }
    ```
    """

    model_config = {"extra": "allow"}
    q: str = Field(..., description="The query to search for.")

    async def run(self) -> tp.AsyncGenerator[ChatCompletionChunk, tp.Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/customsearch/v1?key={os.getenv('SEARCH_ENGINE_API_KEY')}&cx={os.getenv('SEARCH_ENGINE_ID')}&q={self.q}"
            )
            response_json = response.json()
            yield self._parse_chunk(json.dumps(response_json))


class DeepResearch(OpenAITool):
    """
    DeepResearch
    ----------------------
    **Description**: This tool orchestrates a more complex, multi-step research process. It takes a sequence of messages, which can include user queries, assistant thoughts, and tool usage instructions, and executes them using available tools. This allows for iterative refinement of the research process to achieve a comprehensive answer.

    **Input**:
    - `model`: The language model to use for this research run (string, optional). Defaults to `gemini-2.5-pro-preview-05-06`. Available options: `gemini-2.5-flash-preview-05-20`, `gemini-2.5-pro-preview-05-06`.
    - `messages`: A list of messages (list of dictionaries, required). Each message should follow the OpenAI ChatCompletion API format (e.g., `{"role": "user", "content": "..."}`). This sequence of messages guides the research.
    - `tools`: A list of tool definitions (list of dictionaries, optional). These define the tools that can be used during the research process. By default, it includes the definitions of all `OpenAITool` subclasses.
    - `max_tokens`: The maximum number of tokens to generate in the research run (integer, optional). Defaults to `65536`.

    **Output**:
    - A stream of text chunks representing the output of the deep research process, which might include intermediate thoughts, tool calls, and the final answer. Each chunk is part of a `ChatCompletionChunkTypedDict`.

    **Workflow**:
    The `messages` should represent a conversation where the assistant can decide to use the provided `tools`. The process continues until a concluding message is reached or the `max_tokens` limit is hit.

    **Model Information**:
    - `gemini-2.5-flash-preview-05-20`: Suitable for faster, less complex tasks.
    - `gemini-2.5-pro-preview-05-06`: Recommended for more detailed and comprehensive research.

    **Example Usage**:
    ```json
    {
      "messages": [
        {"role": "user", "content": "Find the top 3 tourist attractions in Paris and provide a brief description of each."},
        {"role": "assistant", "content": "I will use Google Search to find this information."}
      ],
      "tools": [
        {
          "type": "function",
          "function": {
            "name": "GoogleSearch",
            "description": "Performs a Google search to retrieve relevant web results.",
            "parameters": {
              "type": "object",
              "properties": {
                "q": {
                  "type": "string",
                  "description": "The query to search for."
                }
              },
              "required": ["q"]
            }
          }
        }
      ]
    }
    ```
    """

    model_config = {"extra": "allow"}
    model: tp.Literal[
        "gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-06-05"
    ] = Field(
        default="gemini-2.5-pro-preview-06-05",
        description="The model to use for the chat completion.",
    )
    messages: tp.List[ChatCompletionMessageParam] = Field(
        ..., description="The messages to guide the deep research process."
    )
    tools: tp.List[ChatCompletionToolParam] = Field(
        default=[t.tool_definition() for t in OpenAITool.__subclasses__()],
        description="The tools that the model can utilize during the research.",
    )
    max_tokens: int = Field(default=65_536)
    tool_choice: ChatCompletionToolChoiceOptionParam = Field(default="auto")
    stream: bool = Field(default=True)

    async def run(self) -> tp.AsyncGenerator[ChatCompletionChunk, tp.Any]:
        client = self.__load__()
        response = await client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
            max_completion_tokens=self.max_tokens,
            stream=True,
            tool_choice=self.tool_choice,
        )
        string = ""
        async for chunk in response:
            calls = chunk.choices[0].delta.tool_calls
            if calls is None or len(calls) == 0:
                content = chunk.choices[0].delta.content
                if not content:
                    continue
                yield self._parse_chunk(content)
                string += content
            else:
                for call in calls:
                    if (
                        not call.function
                        or not call.function.name
                        or not call.function.arguments
                    ):
                        continue
                    tool_class = next(
                        (
                            t
                            for t in OpenAITool.__subclasses__()
                            if t.__name__ == call.function.name
                        ),
                        None,
                    )
                    if tool_class is None:
                        content = call.function.arguments
                        yield self._parse_chunk(content)
                        string += content
                    else:
                        tool = tool_class.model_validate(
                            json.loads(call.function.arguments)
                        )
                        # Recursive call to DeepResearch
                        async for inner_chunk in tool.run():
                            data = inner_chunk.choices[0].delta.content
                            if not data:
                                continue
                            else:
                                string += data
                            self.messages.append({"role": "system", "content": string})
                            string = ""
                            async for inner_chunk in self.run():
                                yield inner_chunk
                            
    def _parse_chunk(self, chunk: str):
        if self.messages[-1]["role"] == "assistant":
            return ChatCompletionChunk(
                id=str(uuid.uuid4()),
                choices=[
                    Choice(delta=ChoiceDelta(content=chunk, role="assistant"), index=0)
                ],
                created=int(time.time()),
                model=self.model,
                object="chat.completion.chunk",
            )
        else:
            return ChatCompletionChunk(
                id=str(uuid.uuid4()),
                choices=[Choice(delta=ChoiceDelta(content=chunk), index=0)],
                created=int(time.time()),
                model=self.model,
                object="chat.completion.chunk",
            )

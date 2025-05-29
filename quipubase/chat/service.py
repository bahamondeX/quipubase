import typing as tp
import httpx
import json
import os
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai._utils._proxy import LazyProxy
from openai import AsyncOpenAI

T = tp.TypeVar("T")

class Tool(BaseModel, LazyProxy[T], ABC):
    """Base Tool class for all vendors tool framework implementations"""

    @classmethod
    def tool_definition(cls) -> ChatCompletionToolParam:
        return ChatCompletionToolParam(
            type="function",
            function={
                "name": cls.__name__,
                "description": cls.__doc__ or "",
                "parameters": cls.model_json_schema().get("properties", {}),
            }
        )
    
    @abstractmethod
    def run(self) -> tp.AsyncGenerator[str, tp.Any]:
        raise NotImplementedError

    @abstractmethod
    def __load__(self) -> T:
        raise NotImplementedError


class OpenAITool(Tool[AsyncOpenAI]):
    @abstractmethod
    def run(self)->tp.AsyncGenerator[str, tp.Any]:
        raise NotImplementedError
    
    def __load__(self):
        return AsyncOpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL"))

class GoogleSearch(OpenAITool):
    """
    GoogleSearch
    ------------
    This tool performs a Google search to retrieve relevant web results based on a given query when the possible answers are not in your training data or cutoff date.
    **Cut-off date**: `2025 May 05`
    """
    q: str = Field(..., description="The query to search for.")

    async def run(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://www.googleapis.com/customsearch/v1?key={os.getenv('SEARCH_ENGINE_API_KEY')}&cx={os.getenv('SEARCH_ENGINE_ID')}&q={self.q}")
            data = response.json()
            yield json.dumps(data)


class CodeCompletion(OpenAITool):
    """
    CodeCompletion
    --------------
    This tool performs a code completion on `Nuxt 3` sandbox by providing the `filePath:str` (~/{type}/{filename}) if type is in ('component','composable','styles') if its an edit the path is inferred, `type:str enum['component','composable','style','edit'], `context?:str` is it's an edit with previous content. Then with this metadata, the coding agent generated the code on the proper location within the sandbox. It can be used multiple times within an LLM run to perform a coding task and generate multiple artifacts.
    """
    type:tp.Literal["component","composable","style","edit"]


class LLMRun(OpenAITool):
    """
    LLMRun
    ----------------------
    `gemini-2.5-flash-preview-05-20` is the default model for free tier users.
    `gemini-2.5-pro-preview-05-06` is the default model for paid users.

    Large Language Model Run is a tool that lets LLM perform a long running task using a set of tools and a sequence of messages. The messages must be fulfilled with the chain of thoughts, where the LLM prompts engineer and evaluates itself with the "user"'s message and answers with the "assistant"'s message on each step until the task is fulfilled. Fullfillment conditions are met with a `Thank you, the task is completed now` as the last message.
    """
    model: tp.Literal["gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-05-06"] = Field(default="gemini-2.5-flash-preview-05-20", description="The model to use for the chat completion.")
    messages: tp.List[ChatCompletionMessageParam] = Field(..., description="The messages to send to the model.")
    tools:tp.List[ChatCompletionToolParam] = Field(default=[t.tool_definition() for t in OpenAITool.__subclasses__()], description="The tools that can be used by the assistant.")
    async def run(self):
        client = self.__load__()
        response = await client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
            stream=True
        )
        async for chunk in response:
            string = ""
            calls = chunk.choices[0].delta.tool_calls
            if not calls:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
                    string += content
                continue
            for call in calls:
                if not call.function or not call.function.name or not json.loads(call.function.arguments):
                    continue
                tool_class = next((t for t in OpenAITool.__subclasses__() if t.__name__ == call.function.name), None)
                if tool_class is None:
                    continue
                tool = tool_class.model_validate(json.loads(call.function.arguments))
                async for chunk in tool.run():
                    yield chunk
                    string += chunk
            self.messages.append({"role": "assistant", "content": string})

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


class ChatCompletion(BaseModel):
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
	tools: tp.Optional[tp.List[ChatCompletionToolParam]] = Field(	
		default=None,
		description="The tools that the model can utilize during the research.",
	)
	tool_choice: ChatCompletionToolChoiceOptionParam = Field(default="auto")
	stream: bool = Field(default=True)
	max_tokens: int = Field(
		default=65536,
		description="The maximum number of tokens to generate in the research run.",
	)

		
	async def run(self):
		client = AsyncOpenAI()
		if self.stream is False:
			return await client.chat.completions.create(
				model=self.model,
				messages=self.messages,
				tools=self.tools or [],
				tool_choice=self.tool_choice,
				max_tokens=self.max_tokens,
				stream=False,
			)
		else:
			return await client.chat.completions.create(
			model=self.model,
			messages=self.messages,
			tools=self.tools or [],
			tool_choice=self.tool_choice,
			stream=True,
			max_tokens=self.max_tokens,
		)
							
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

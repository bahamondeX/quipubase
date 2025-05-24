import typing as tp

from typing_extensions import NotRequired, Required, TypedDict


class MessageCreateParam(TypedDict): ...


class ChatCompletionParams(TypedDict):
    model: tp.Literal["gemini-2.5-flash-preview-05-20"]
    contents: tp.List[MessageCreateParam]

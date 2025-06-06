import typing as tp

from fastapi import APIRouter


def route():
    app = APIRouter(prefix="/models", tags=["models"])

    @app.get("")
    def _() -> dict[str, tp.Any]:
        return {
            "data": [
                {
                    "id": "gemini-2.5-flash-preview-05-20",
                    "created": 1693721698,
                    "object": "model",
                    "owned_by": "Google",
                    "active": True,
                    "context_window": 1000000,
                    "public_apps": None,
                    "max_completion_tokens": 65_536,
                },
                {
                    "id": "gemini-2.5-pro-preview-05-06",
                    "created": 1693721698,
                    "object": "model",
                    "owned_by": "Google",
                    "active": True,
                    "context_window": 1000000,
                    "public_apps": None,
                    "max_completion_tokens": 65_536,
                },
            ],
            "object": "list",
        }

    @app.get("/{model}")
    def _(model: str) -> dict[str, tp.Any]:
        return {
            "id": model,
            "created": 1693721698,
            "object": "model",
            "owned_by": "Google",
            "active": True,
            "context_window": 1000000,
            "public_apps": None,
            "max_completion_tokens": 65_536,
        }

    return app

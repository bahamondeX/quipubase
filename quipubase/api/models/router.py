import typing as tp

from fastapi import APIRouter


def route():
    app = APIRouter(prefix="/models", tags=["models"])

    @app.get("")
    def _() -> dict[str, tp.Any]:
        return {
            "data": [
                {
                    "id": id,
                    "created": 1693721698,
                    "object": "model",
                    "owned_by": "Google",
                    "active": True,
                    "context_window": 1000000,
                    "public_apps": None,
                    "max_completion_tokens": 8192,
                }
                for id in [
                    "gemini-2.5-flash",
                    "gemini-2.0-flash",
                ]
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
            "max_completion_tokens": 8192,
        }

    return app

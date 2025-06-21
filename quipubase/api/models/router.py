import typing as tp

from fastapi import APIRouter, HTTPException
from groq import AsyncGroq

ai = AsyncGroq()

MAPPING: dict[str, str] = {
    "llama-3.3-70b-versatile": "versatile",
    "llama-3.1-8b-instant": "instant",
    "meta-llama/llama-4-scout-17b-16e-instruct": "scout",
    "meta-llama/llama-4-maverick-17b-128e-instruct": "maverick",
}

REVERSE_MAPPING = {v: k for k, v in MAPPING.items()}


def route():
    app = APIRouter(prefix="/models", tags=["models"])

    @app.get("")
    async def list_models():
        response = await ai.models.list()
        filtered = []

        for model in response.data:
            if model.id in MAPPING:
                model.id = MAPPING[model.id]  # replace ID with alias
                filtered.append(model)

        return {
            "object": "list",
            "data": [m.model_dump(exclude_none=True) for m in filtered],
        }

    @app.get("/{model}")
    async def get_model(model: str):
        original_id = REVERSE_MAPPING.get(model)
        if not original_id:
            raise HTTPException(status_code=404, detail="Model not found")

        response = await ai.models.retrieve(model=original_id)
        response.id = MAPPING[original_id]
        return response.model_dump(exclude_none=True)

    return app

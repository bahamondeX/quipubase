from fastapi import APIRouter

from .service import ImageGenerationRequest

app = APIRouter(prefix="/generations", tags=["images"])


@app.post("")
async def image_generation_endpoint(request: ImageGenerationRequest):
    return await request.create()

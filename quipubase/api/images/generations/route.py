from fastapi import APIRouter

from .service import ImageGenerateParams, ImageGenerationService

app = APIRouter(prefix="/generations", tags=["images"])
service = ImageGenerationService()

@app.post("")
async def image_generation_endpoint(request: ImageGenerateParams):
    return await service.run(request)

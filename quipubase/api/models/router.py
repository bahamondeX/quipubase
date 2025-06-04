from openai import AsyncOpenAI
from fastapi import APIRouter
from dotenv import load_dotenv



def route():
	load_dotenv()
	app = APIRouter(prefix="/models", tags=["models"])

	ai = AsyncOpenAI()

	@app.get("/")
	async def _():
		return await ai.models.list()

	@app.get("/{model}")
	async def _(model: str):
		return await ai.models.retrieve(model)

	return app

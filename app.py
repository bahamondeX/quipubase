import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException

load_dotenv()

app = FastAPI()
auth = APIRouter(tags=["Auth"], prefix="/auth")


@auth.get("/github")
async def _(code: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": os.getenv("GH_CLIENT_ID"),
                "client_secret": os.getenv("GH_CLIENT_SECRET"),
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)


app.include_router(auth, prefix="/v1")

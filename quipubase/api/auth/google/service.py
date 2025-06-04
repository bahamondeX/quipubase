import asyncio
import json
import os
import typing as tp
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import typing_extensions as tpe
from dotenv import load_dotenv
from httpx import AsyncClient

from quipubase.lib.cache import db

from .typedefs import GoogleAuthResponse, GoogleTokenResponse, GoogleUser

load_dotenv()


class RequestData(tp.TypedDict):
    url: tpe.Required[str]
    method: tpe.Required[tp.Literal["GET", "POST"]]
    headers: tpe.NotRequired[dict[str, str]]
    params: tpe.NotRequired[dict[str, str]]
    data: tpe.NotRequired[dict[str, tp.Any]]
    json: tpe.NotRequired[dict[str, tp.Any]]
    files: tpe.NotRequired[dict[str, tp.Any]]
    timeout: tpe.NotRequired[float]


@dataclass
class APIClient:
    base_url: str
    headers: dict[str, str]

    def __hash__(self):
        return int(sha256(json.dumps(asdict(self)).encode()).hexdigest(), 16)

    def _client(self):
        return AsyncClient(base_url=self.base_url, headers=self.headers)

    async def fetch(self, **kwargs: tpe.Unpack[RequestData]):
        response = await self._client().request(**kwargs)
        response.raise_for_status()
        return response


@dataclass
class AuthGoogleClient(APIClient):
    base_url: str = field(default="https://oauth2.googleapis.com", repr=False)
    headers: dict[str, str] = field(
        default_factory=lambda: {"Accept": "application/json"}, repr=False
    )

    async def authorize(self, code: str) -> GoogleTokenResponse:
        response = await self.fetch(
            url="/token",
            method="POST",
            data={
                "code": code,
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return GoogleTokenResponse.model_validate(response.json())

    async def refresh_token(self, access_token: str) -> GoogleTokenResponse:
        response = await self.fetch(
            url="/token",
            method="POST",
            data={
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "access_token": access_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return GoogleTokenResponse.model_validate(response.json())

    async def user_info(self, access_token: str):
        response = await self.fetch(
            url="/oauth2/v3/userinfo",
            method="GET",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


@dataclass
class AuthGoogleUserClient(APIClient):
    base_url: str = field(default="https://www.googleapis.com", repr=False)
    headers: dict[str, str] = field(
        default_factory=lambda: {"Accept": "application/json"}, repr=False
    )

    async def user_info(self, access_token: str):
        response = await self.fetch(
            url="/oauth2/v3/userinfo",
            method="GET",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


@dataclass
class GoogleAuthService:
    google_client: AuthGoogleClient = field(default_factory=AuthGoogleClient)
    google_user_client: AuthGoogleUserClient = field(
        default_factory=AuthGoogleUserClient
    )

    async def run(self, code: str) -> GoogleAuthResponse:
        token = await self.google_client.authorize(code)
        await self.store_token(token)
        user = await self.user_info(token.access_token)
        return GoogleAuthResponse(
            tokenInfo=token, userInfo=GoogleUser.model_validate(user)
        )

    async def user_info(self, access_token: str) -> dict[str, tp.Any]:
        return await self.google_user_client.user_info(access_token)

    async def refresh_token(self, access_token: str) -> GoogleTokenResponse:
        token = await self.google_client.refresh_token(access_token)
        await self.store_token(token)
        return token

    async def store_token(self, token: GoogleTokenResponse):
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(seconds=token.expires_in)

        key = f"google:token:{token.access_token}"
        payload: dict[str, object] = {
            "access_token": token.access_token,
            "id_token": token.id_token,
            "expires_in": token.expires_in,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        await db.set(key, json.dumps(payload))
        await db.expireat(key, int(expires_at.timestamp()))

        self.schedule_token_refresh(token)

    def schedule_token_refresh(self, token: GoogleTokenResponse):
        delay = token.expires_in - 60
        asyncio.create_task(self._schedule_refresh(token.access_token, delay))

    async def _schedule_refresh(self, access_token: str, delay: float):
        await asyncio.sleep(delay)
        new_token = await self.refresh_token(access_token)
        await self.store_token(new_token)

    async def resume_scheduled_refreshes(self):
        pattern = "google:token:*"
        async for key in db.scan_iter(match=pattern):
            value = await db.get(key)
            if not value:
                continue
            try:
                data = json.loads(value)
                access_token = data["access_token"]
                expires_at = datetime.fromisoformat(data["expires_at"])
                delay = (expires_at - datetime.now(timezone.utc)).total_seconds() - 60
                if delay > 0:
                    asyncio.create_task(self._schedule_refresh(access_token, delay))
            except Exception as e:
                print(f"[token-refresh] Error reloading key {key}: {e}")

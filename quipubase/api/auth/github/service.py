import asyncio
import json
import os
import typing as tp
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import typing_extensions as tpe
from dotenv import load_dotenv
from httpx import AsyncClient, Response
from openai._utils._proxy import LazyProxy

from quipubase.lib.cache import load_cache

db = load_cache()

from .typedefs import GithubAuthResponse, GitHubTokenResponse, GitHubUser

load_dotenv()


class RequestData(tp.TypedDict, total=False):
    url: tpe.Required[str]
    method: tpe.Required[
        tp.Literal["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH", "OPTIONS", "TRACE"]
    ]
    headers: dict[str, str]
    params: dict[str, str]
    data: dict[str, tp.Any]
    json: dict[str, tp.Any]
    files: dict[str, tp.Any]
    timeout: float


@dataclass(eq=False)
class APIClient(LazyProxy[AsyncClient]):
    base_url: str
    headers: dict[str, str]

    def __hash__(self):
        return int(
            sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest(), 16
        )

    def __load__(self) -> AsyncClient:
        return AsyncClient(base_url=self.base_url, headers=self.headers)

    async def fetch(self, **kwargs: tpe.Unpack[RequestData]) -> Response:
        async with self.__load__() as client:
            response = await client.request(**kwargs)
            response.raise_for_status()
            return response


@dataclass
class AuthGithubClient(APIClient):
    base_url: str = field(default="https://github.com", repr=False)
    headers: dict[str, str] = field(
        default_factory=lambda: {"Accept": "application/json"}, repr=False
    )

    async def authorize(self, code: str) -> GitHubTokenResponse:
        response = await self.fetch(
            url="https://github.com/login/oauth/access_token",
            method="POST",
            data={
                "client_id": os.getenv("GH_CLIENT_ID"),
                "client_secret": os.getenv("GH_CLIENT_SECRET"),
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        return GitHubTokenResponse.model_validate(response.json())


@dataclass
class AuthGithubUserClient(APIClient):
    base_url: str = field(default="https://api.github.com", repr=False)
    headers: dict[str, str] = field(
        default_factory=lambda: {"Accept": "application/json"}, repr=False
    )

    async def user_info(self, access_token: str):
        response = await self.fetch(
            url="https://api.github.com/user",
            method="GET",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


@dataclass
class GithubAuthService:
    github_client: AuthGithubClient = field(default_factory=AuthGithubClient)
    github_user_client: AuthGithubUserClient = field(
        default_factory=AuthGithubUserClient
    )

    async def run(self, code: str) -> GithubAuthResponse:
        token = await self.github_client.authorize(code)
        await self.store_token(token)
        user = await self.user_info(token.access_token)
        return GithubAuthResponse(
            tokenInfo=token, userInfo=GitHubUser.model_validate(user)
        )

    async def user_info(self, access_token: str):
        return await self.github_user_client.user_info(access_token)

    async def refresh_token(self, refresh_token: str) -> GitHubTokenResponse:
        response = await self.github_client.fetch(
            url="https://github.com/login/oauth/access_token",
            method="POST",
            data={
                "client_id": os.getenv("GH_CLIENT_ID"),
                "client_secret": os.getenv("GH_CLIENT_SECRET"),
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Accept": "application/json"},
        )
        token = GitHubTokenResponse.model_validate(response.json())
        asyncio.create_task(self.store_token(token))
        user = await self.user_info(token.access_token)
        return GithubAuthResponse(tokenInfo=token, userInfo=user)  # type: ignore

    async def store_token(self, token: GitHubTokenResponse) -> None:
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(seconds=token.expires_in)

        key = f"github:token:{token.access_token}"
        payload: dict[str, object] = {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_in": token.expires_in,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        await db.set(key, json.dumps(payload))  # type: ignore
        await db.expireat(key, int(expires_at.timestamp()))  # type: ignore
        self.schedule_token_refresh(token)

    async def resume_scheduled_refreshes(self) -> None:
        pattern = "github:token:*"
        async for key in db.scan_iter(match=pattern):  # type: ignore
            value = await db.get(key)  # type: ignore
            if not value:
                continue
            try:
                data = json.loads(value)  # type: ignore
                refresh_token = data["refresh_token"]
                expires_at = datetime.fromisoformat(data["expires_at"])
                delay = (expires_at - datetime.now(timezone.utc)).total_seconds() - 60
                if delay > 0:
                    asyncio.create_task(self._schedule_refresh(refresh_token, delay))
            except Exception as e:
                print(f"[token-refresh] Error reloading key {key}: {e}")

    def schedule_token_refresh(self, token: GitHubTokenResponse) -> None:
        delay = token.expires_in - 60
        asyncio.create_task(self._schedule_refresh(token.refresh_token, delay))

    async def _schedule_refresh(self, refresh_token: str, delay: float) -> None:
        await asyncio.sleep(max(0, delay))
        new_token = await self.refresh_token(refresh_token)
        await self.store_token(new_token)

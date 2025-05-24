import os
import typing as tp
from urllib.parse import urlencode

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import RedirectResponse

from . import GithubAuthService, GoogleAuthService

APP_URL: str = "http://localhost:3500"


def route():
    auth = APIRouter(tags=["auth"], prefix="/auth")
    gh = GithubAuthService()
    gg = GoogleAuthService()

    @auth.get("/{provider}", response_class=RedirectResponse)
    async def _(
        request: Request,
        code: tp.Optional[str] = Query(default=None),
        provider: tp.Literal["github", "google"] = Path(...)
    ):
        if provider == "github" and code:
            redirect_url = request.cookies.get("redirect_url") or APP_URL
            res = await gh.run(code)
            query_params = {
                "name": res.userInfo.name,
                "sub": res.userInfo.sub,
                "picture": res.userInfo.picture,
                "access_token": res.tokenInfo.access_token,
            }
            return RedirectResponse(url=f"{redirect_url}?{urlencode(query_params)}")
        if provider == "google" and code:
            redirect_url = request.cookies.get("redirect_url") or APP_URL
            res = await gg.run(code)
            query_params = {
                "name": res.userInfo.name,
                "sub": res.userInfo.sub,
                "picture": res.userInfo.picture,
                "access_token": res.tokenInfo.access_token,
            }
            return RedirectResponse(url=f"{redirect_url}?{urlencode(query_params)}")
        if provider == "github":
            return RedirectResponse(
                url=f"https://github.com/login/oauth/authorize?client_id={os.getenv('GH_CLIENT_ID')}"
            )
        return RedirectResponse(
            url=f"https://accounts.google.com/o/oauth2/v2/auth?client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&response_type=code&scope=openid%20email%20profile"
        )

    return auth

import typing as tp
import os

from fastapi import APIRouter, Path, Query
from fastapi.responses import RedirectResponse

from ..auth import GithubAuthService, GoogleAuthService


def auth_router():
    auth = APIRouter(tags=["auth"], prefix="/auth")
    gh = GithubAuthService()
    gg = GoogleAuthService()

    @auth.get("/{provider}")
    async def _(code: tp.Optional[str]=Query(default=None), provider: tp.Literal["github", "google"]=Path(...)):
        if provider == 'github' and code:
            return await gh.run(code)
        if provider == 'google' and code:
            return await gg.run(code)
        if provider == 'github':
            return RedirectResponse(
                url=f"https://github.com/login/oauth/authorize?client_id={os.getenv('GH_CLIENT_ID')}"
            )
        return RedirectResponse(
                url=f"https://accounts.google.com/o/oauth2/v2/auth?client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&response_type=code&scope=openid%20email%20profile"
            )

    return auth

# models/google_auth.py
import typing as tp
from typing import Optional

from pydantic import BaseModel, Field


class GoogleTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str
    token_type: str
    id_token: Optional[str]


class GoogleUser(BaseModel):
    model_config = {"extra": "allow"}
    sub: str = Field(...)
    name: str = Field(...)
    picture: str = Field(
        default="https://lh3.googleusercontent.com/a/default-user=s96-c"
    )
    email: str = Field(...)
    email_verified: bool = Field(...)


class GoogleAuthResponse(BaseModel):
    tokenInfo: GoogleTokenResponse
    userInfo: GoogleUser

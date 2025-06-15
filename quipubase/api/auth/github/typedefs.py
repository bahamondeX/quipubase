import base64c as base64
import typing as tp
from datetime import datetime

from pydantic import BaseModel, computed_field


class GitHubTokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str
    refresh_token: str
    expires_in: int
    refresh_token_expires_in: int


class SessionData(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    refresh_expires_at: datetime
    user_id: str


class GitHubUser(BaseModel):
    model_config = {"extra": "allow"}
    login: str
    id: int
    avatar_url: str
    url: str
    html_url: str
    type: str
    site_admin: bool

    @computed_field(return_type=str)
    @property
    def sub(self):
        return (
            "gh-"
            + base64.b64encode(str(self.id).encode() + self.login.encode()).decode()
        )

    @computed_field(return_type=str)
    @property
    def picture(self):
        return self.avatar_url

    @computed_field(return_type=str)
    @property
    def name(self):
        return self.login


class GithubAuthResponse(BaseModel):
    tokenInfo: GitHubTokenResponse
    userInfo: GitHubUser

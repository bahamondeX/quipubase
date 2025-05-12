from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi import Depends, HTTPException, status, Request, Response, FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import secrets
import time
from typing import Dict, Optional
import uuid

BASE_URL = "http://localhost:5454"

# In-memory storage (replace with a database in production)
auth_codes = {}  # code -> {client_id, redirect_uri, expires, user_id}
tokens = {}      # token -> {client_id, user_id, scope, expires}
clients = {
    "example_client": {
        "client_secret": "example_secret",
        "redirect_uris": ["http://localhost:8000/callback"]
    }
}

class OAuth2Config(BaseModel):
    authorizationUrl: str
    tokenUrl: str

    @property
    def oauth2(self):
        return OAuth2AuthorizationCodeBearer(
            authorizationUrl=self.authorizationUrl,
            tokenUrl=self.tokenUrl,
        )

class AuthorizeRequest(BaseModel):
    response_type: str
    client_id: str
    redirect_uri: str
    scope: Optional[str] = ""
    state: Optional[str] = None

class TokenRequest(BaseModel):
    grant_type: str
    code: str
    redirect_uri: str
    client_id: str
    client_secret: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

oauth2_config = OAuth2Config(authorizationUrl=f"{BASE_URL}/oauth/authorize", tokenUrl=f"{BASE_URL}/oauth/token")

app = FastAPI()

# Simulate user authentication
async def get_current_user():
    # In production, implement real user authentication
    return {"id": "user123", "name": "Test User"}

@app.get("/oauth/authorize")
async def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str = "",
    state: Optional[str] = None
):
    # Validate client
    if client_id not in clients:
        raise HTTPException(status_code=400, detail="Invalid client")
    
    # Validate redirect URI
    if redirect_uri not in clients[client_id]["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid redirect URI")
    
    # In a real app, authenticate the user here
    user = await get_current_user()
    
    # Generate authorization code
    code = secrets.token_urlsafe(32)
    
    # Store the code (with 10 minute expiration)
    auth_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "expires": time.time() + 600,
        "user_id": user["id"],
        "scope": scope
    }
    
    # Redirect back to client with code
    redirect_url = f"{redirect_uri}?code={code}"
    if state:
        redirect_url += f"&state={state}"
    
    return RedirectResponse(redirect_url)

@app.post("/oauth/token", response_model=TokenResponse)
async def token(request: TokenRequest):
    # Validate client credentials
    if request.client_id not in clients:
        raise HTTPException(status_code=400, detail="Invalid client")
    
    if clients[request.client_id]["client_secret"] != request.client_secret:
        raise HTTPException(status_code=400, detail="Invalid client secret")
    
    # Validate grant type
    if request.grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant type")
    
    # Validate code
    code_data = auth_codes.pop(request.code, None)
    if not code_data:
        raise HTTPException(status_code=400, detail="Invalid code")
    
    # Check if code is expired
    if code_data["expires"] < time.time():
        raise HTTPException(status_code=400, detail="Code expired")
    
    # Check if redirect URI matches
    if code_data["redirect_uri"] != request.redirect_uri:
        raise HTTPException(status_code=400, detail="Redirect URI mismatch")
    
    # Generate access token
    access_token = str(uuid.uuid4())
    refresh_token = str(uuid.uuid4())
    expires_in = 3600  # 1 hour
    
    # Store token
    tokens[access_token] = {
        "client_id": request.client_id,
        "user_id": code_data["user_id"],
        "scope": code_data.get("scope", ""),
        "expires": time.time() + expires_in
    }
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        refresh_token=refresh_token,
        scope=code_data.get("scope", "")
    )

# Protected resource example
@app.get("/api/me")
async def get_me(token: str = Depends(oauth2_config.oauth2)):
    # Validate token
    token_data = tokens.get(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if token is expired
    if token_data["expires"] < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return user info
    return {"user_id": token_data["user_id"], "scope": token_data["scope"]} 
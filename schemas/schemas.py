from pydantic import BaseModel
from typing import Optional, List


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    refresh_token: Optional[str]


class RefreshRequest(BaseModel):
    refresh_token: str


class ChatMessage(BaseModel):
    message: str


class ChatAction(BaseModel):
    type: str
    target: str
    packages: Optional[List[str]] = None
    scheme: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    action: ChatAction | None = None

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from controllers.auth_controller import register_controller, login_controller
from services.assistant_service import get_current_user, refresh_access_token, revoke_refresh_token, oauth2_scheme, revoke_token
from fastapi import Response
from fastapi.responses import StreamingResponse
from io import BytesIO
try:
    from gtts import gTTS
except Exception:
    gTTS = None
from schemas.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, RefreshRequest

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/register", response_model=UserResponse)
def register_route(payload: UserCreate):
    res = register_controller(payload.username, payload.email, payload.password)
    if res is None or res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("error", "register_failed"))
    return {"id": res["id"], "username": res["username"], "email": res.get("email")}


@router.post("/login", response_model=TokenResponse)
def login_route(payload: UserLogin):
    res = login_controller(payload.username, payload.password)
    if res is None:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    return res


@router.post("/refresh", response_model=TokenResponse)
def refresh_route(payload: RefreshRequest):
    res = refresh_access_token(payload.refresh_token)
    if res is None:
        raise HTTPException(status_code=401, detail="invalid_refresh_token")
    return res


@router.post("/logout")
def logout_route(
    payload: Optional[dict] = None,
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(get_current_user),
):
    ok_access = revoke_token(token)
    ok_refresh = None
    if payload and isinstance(payload, dict):
        rt = payload.get("refresh_token")
        if rt:
            ok_refresh = revoke_refresh_token(rt)
    return {"revoked": True, "revoked_access": ok_access, "revoked_refresh": ok_refresh}


@router.get("/me")
def me_route(current_user: dict = Depends(get_current_user)):
    # return basic user info plus a greeting text
    user = {"id": current_user.get("id"), "username": current_user.get("username"), "email": current_user.get("email")}
    greeting = f"Selamat datang, {user['username']}"
    return {"user": user, "greeting": greeting}


@router.get("/greeting/audio")
def greeting_audio(current_user: dict = Depends(get_current_user)):
    # return an MP3 audio stream saying the greeting (requires gTTS installed)
    if gTTS is None:
        raise HTTPException(status_code=501, detail="gTTS library not installed on server")
    text = f"Selamat datang, {current_user.get('username')}"
    buf = BytesIO()
    tts = gTTS(text=text, lang="id")
    tts.write_to_fp(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="audio/mpeg")

from dotenv import load_dotenv
import os
import hashlib
import secrets
import time
from typing import Optional, Tuple
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
import uuid

# keep only authentication-related helpers
from models import users_model

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
REFRESH_TOKEN_EXPIRE_DAYS = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/assistant/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = uuid.uuid4().hex
    to_encode.update({"exp": expire, "iat": now, "jti": jti, "sub": to_encode.get("sub")})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token(user_id: int) -> Tuple[str, Optional[dict]]:
    plain = secrets.token_urlsafe(64)
    token_hash = _hash_token(plain)
    now = int(time.time())
    expires_at = now + REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    rec = users_model.store_refresh_token(user_id, token_hash, now, expires_at)
    return plain, rec


def verify_refresh_token(plain_token: str) -> Optional[dict]:
    token_hash = _hash_token(plain_token)
    rec = users_model.find_refresh_token(token_hash)
    if not rec:
        return None
    if rec.get("revoked"):
        return None
    if rec.get("expires_at") and rec.get("expires_at") < int(time.time()):
        return None
    return rec


def refresh_access_token(refresh_token: str) -> Optional[dict]:
    rec = verify_refresh_token(refresh_token)
    if rec is None:
        return None
    user = users_model.find_user_by_id(rec["user_id"]) if hasattr(users_model, "find_user_by_id") else None
    if user is None:
        # fallback: query sqlite directly using users_model.DB_PATH
        try:
            import sqlite3

            conn = sqlite3.connect(users_model.DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT id, username, email FROM users WHERE id = ?", (rec["user_id"],))
            row = cur.fetchone()
            if row is None:
                return None
            user = {"id": row["id"], "username": row["username"], "email": row["email"]}
        finally:
            try:
                conn.close()
            except Exception:
                pass
    users_model.revoke_refresh_token(_hash_token(refresh_token))
    new_plain, _ = create_refresh_token(user["id"])
    access = create_access_token({"sub": user["username"], "id": user["id"]})
    return {"access_token": access, "token_type": "bearer", "refresh_token": new_plain, "user": user}


def revoke_refresh_token(plain_token: str) -> bool:
    token_hash = _hash_token(plain_token)
    return users_model.revoke_refresh_token(token_hash)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        jti = payload.get("jti")
        if jti and users_model.is_token_revoked(jti):
            raise HTTPException(status_code=401, detail="token_revoked")
        if username is None:
            raise HTTPException(status_code=401, detail="invalid_token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid_token")
    user = users_model.find_user(username)
    if user is None:
        raise HTTPException(status_code=401, detail="user_not_found")
    return user


def revoke_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
    except jwt.PyJWTError:
        return False
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti is None or exp is None:
        return False
    try:
        exp_int = int(exp)
    except Exception:
        exp_int = int(time.time())
    return users_model.revoke_token(jti, exp_int)


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def register_user(username: str, email: str, password: str) -> Optional[dict]:
    existing = users_model.find_user(username)
    if existing is not None:
        return None
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    user = users_model.add_user(username, email, password_hash, salt)
    return user


def authenticate_user(username: str, password: str) -> Optional[dict]:
    u = users_model.find_user(username)
    if u is None:
        return None
    if _hash_password(password, u.get("salt", "")) == u.get("password_hash"):
        return u
    return None


def revoke_refresh_for_user(user_id: int) -> int:
    return users_model.revoke_all_refresh_tokens_for_user(user_id)

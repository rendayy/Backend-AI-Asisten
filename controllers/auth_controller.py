from services.assistant_service import (
    register_user,
    authenticate_user,
    create_access_token,
    create_refresh_token,
)


def register_controller(username: str, email: str, password: str):
    res = register_user(username, email, password)
    if res is None:
        return {"error": "user_exists_or_conflict"}
    return {"id": res["id"], "username": res["username"], "email": res.get("email")}


def login_controller(username: str, password: str):
    u = authenticate_user(username, password)
    if u is None:
        return None
    access_token = create_access_token({"sub": u["username"], "id": u["id"]})
    refresh_plain, _ = create_refresh_token(u["id"])  # store and return plain refresh token
    greeting = f"Selamat datang, {u['username']}"
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_plain,
        "user": {"id": u["id"], "username": u["username"], "email": u.get("email")},
        "greeting": greeting,
    }

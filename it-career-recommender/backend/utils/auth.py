# auth.py
import os
import time
from typing import Any, Dict

import bcrypt
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests as grequests
from google.oauth2 import id_token

from .db import users

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_EXP_SECS = int(os.getenv("JWT_EXP_SECS", "86400"))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

bearer = HTTPBearer(auto_error=False)


# ---------------------------
# User creation / verification
# ---------------------------
async def create_user(name: str, email: str, password: str) -> str:
    """
    Create a new user with bcrypt-hashed password.
    Returns inserted_id as string.
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    doc = {"name": name, "email": email, "password": hashed.decode("utf-8"), "provider": "password"}
    res = await users.insert_one(doc)
    return str(res.inserted_id)


async def verify_user(email: str, password: str) -> Dict[str, Any] | None:
    """
    Verify email/password. Returns user document (dict) if ok, else None.
    """
    u = await users.find_one({"email": email})
    if not u:
        return None

    stored = u.get("password", "")
    # stored may be string; convert to bytes for bcrypt
    try:
        stored_bytes = stored.encode("utf-8") if isinstance(stored, str) else stored
    except Exception:
        stored_bytes = stored

    if not bcrypt.checkpw(password.encode("utf-8"), stored_bytes):
        return None
    return u


async def upsert_google_user(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upsert a Google SSO user from the verified token payload.
    Returns the user document.
    """
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google payload missing email")

    name = payload.get("name") or email.split("@")[0]
    picture = payload.get("picture")

    found = await users.find_one({"email": email})
    if found:
        await users.update_one(
            {"_id": found["_id"]},
            {"$set": {"name": name, "picture": picture, "provider": "google"}},
        )
        return await users.find_one({"_id": found["_id"]})

    res = await users.insert_one({"name": name, "email": email, "provider": "google", "picture": picture})
    return await users.find_one({"_id": res.inserted_id})


# ---------------------------
# JWT helpers
# ---------------------------
def make_token(u: Dict[str, Any]) -> str:
    """
    Create a signed JWT for the given user document.
    """
    uid = u.get("_id") or u.get("id") or u.get("user_id")
    # If it's an ObjectId, stringify it
    if isinstance(uid, ObjectId):
        uid = str(uid)

    payload = {
        "sub": str(uid),
        "email": u.get("email"),
        "name": u.get("name", ""),
        "exp": int(time.time()) + JWT_EXP_SECS,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    # PyJWT >= 2.0 returns a str, earlier versions may return bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


# ---------------------------
# Dependency to fetch current user
# ---------------------------
async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from Bearer token.
    Raises HTTPException if invalid/expired or user not found.
    """
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        obj_id = ObjectId(uid)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id in token")

    u = await users.find_one({"_id": obj_id})
    if not u:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return u


# ---------------------------
# Google ID token verification
# ---------------------------
async def verify_google_id_token(id_tok: str) -> Dict[str, Any]:
    """
    Verify Google ID token server-side and return the payload.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    try:
        payload = id_token.verify_oauth2_token(id_tok, grequests.Request(), GOOGLE_CLIENT_ID)
        # Ensure the token was issued to our client id
        if payload.get("aud") != GOOGLE_CLIENT_ID:
            raise ValueError("Audience mismatch")
        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Google token invalid: {e}")

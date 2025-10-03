import os
import time
from typing import Any, Dict

import bcrypt
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from pydantic import BaseModel, EmailStr

from .db import users, selections

# ---------------------------
# Config
# ---------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_EXP_SECS = int(os.getenv("JWT_EXP_SECS", "86400"))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

bearer = HTTPBearer(auto_error=False)
router = APIRouter()  # add API router

# ---------------------------
# Schemas
# ---------------------------
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ---------------------------
# User creation / verification
# ---------------------------
async def create_user(name: str, email: str, password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    doc = {"name": name, "email": email, "password": hashed.decode("utf-8"), "provider": "password"}
    res = await users.insert_one(doc)
    return str(res.inserted_id)

async def verify_user(email: str, password: str) -> Dict[str, Any] | None:
    u = await users.find_one({"email": email})
    if not u:
        return None

    stored = u.get("password", "")
    stored_bytes = stored.encode("utf-8") if isinstance(stored, str) else stored

    if not bcrypt.checkpw(password.encode("utf-8"), stored_bytes):
        return None
    return u

async def upsert_google_user(payload: Dict[str, Any]) -> Dict[str, Any]:
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
    uid = u.get("_id") or u.get("id") or u.get("user_id")
    if isinstance(uid, ObjectId):
        uid = str(uid)

    payload = {
        "sub": str(uid),
        "email": u.get("email"),
        "name": u.get("name", ""),
        "exp": int(time.time()) + JWT_EXP_SECS,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("utf-8")

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> Dict[str, Any]:
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
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    try:
        payload = id_token.verify_oauth2_token(id_tok, grequests.Request(), GOOGLE_CLIENT_ID)
        if payload.get("aud") != GOOGLE_CLIENT_ID:
            raise ValueError("Audience mismatch")
        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Google token invalid: {e}")

# ---------------------------
# API Routes
# ---------------------------
@router.post("/signup")
async def signup(data: SignupRequest):
    uid = await create_user(data.name, data.email, data.password)
    user = await users.find_one({"_id": ObjectId(uid)})
    token = make_token(user)
    return {"token": token, "user": {"id": uid, "email": data.email, "name": data.name}}

@router.post("/login")
async def login(data: LoginRequest):
    user = await verify_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = make_token(user)
    return {"token": token, "user": {"id": str(user["_id"]), "email": user["email"], "name": user["name"]}}

@router.post("/google-login")
async def google_login(id_token: str):
    payload = await verify_google_id_token(id_token)
    user = await upsert_google_user(payload)
    token = make_token(user)
    return {"token": token, "user": {"id": str(user["_id"]), "email": user["email"], "name": user["name"]}}

@router.get("/dashboard")
async def dashboard(user=Depends(get_current_user)):
    selections_cursor = selections.find({"user_id": str(user["_id"])})
    paths = [s async for s in selections_cursor]
    return {
        "user": {"id": str(user["_id"]), "email": user["email"], "name": user["name"]},
        "resume": user.get("resume"),
        "paths": paths,
    }

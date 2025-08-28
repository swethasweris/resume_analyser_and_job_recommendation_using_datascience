# models.py
from pydantic import BaseModel, EmailStr
from typing import List


class SignupIn(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleSSOIn(BaseModel):
    id_token: str  # Google ID Token from client


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: EmailStr


class ChoosePathIn(BaseModel):
    chosen_path: str
    courses: List[str] = []


class SelectionOut(BaseModel):
    chosen_path: str
    courses: List[str] = []

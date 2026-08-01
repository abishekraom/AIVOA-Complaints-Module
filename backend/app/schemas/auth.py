from pydantic import BaseModel

from app.schemas.user import NormalizedEmail

class LoginRequest(BaseModel):
    email: NormalizedEmail
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SignatureRequest(BaseModel):
    password: str

class SignatureResponse(BaseModel):
    verified: bool

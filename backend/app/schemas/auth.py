from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SignatureRequest(BaseModel):
    password: str

class SignatureResponse(BaseModel):
    verified: bool

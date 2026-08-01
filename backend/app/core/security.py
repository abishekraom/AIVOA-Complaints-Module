import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
BCRYPT_MAX_PASSWORD_BYTES = 72

def hash_password(plain: str) -> str:
    if len(plain.encode()) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"password must be at most {BCRYPT_MAX_PASSWORD_BYTES} bytes")
    return _pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)

# Verified against when no user matches, so an unknown email costs the same
# bcrypt work as a known email with the wrong password (no timing oracle).
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

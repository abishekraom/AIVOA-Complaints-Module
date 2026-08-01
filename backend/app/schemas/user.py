import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.models.user import Role

# Account identity is case-insensitive; the DB unique index is not, so every
# email crossing the API boundary is folded to lowercase here.
NormalizedEmail = Annotated[EmailStr, AfterValidator(str.lower)]

BCRYPT_MAX_PASSWORD_BYTES = 72

def _within_bcrypt_limit(value: str) -> str:
    # bcrypt silently truncates beyond 72 *bytes*, not characters.
    if len(value.encode()) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"password must be at most {BCRYPT_MAX_PASSWORD_BYTES} bytes")
    return value

Password = Annotated[str, Field(min_length=12), AfterValidator(_within_bcrypt_limit)]

class UserCreate(BaseModel):
    email: NormalizedEmail
    password: Password
    full_name: str
    role: Role

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: Role

    model_config = {"from_attributes": True}

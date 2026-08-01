import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.models.user import Role

# Account identity is case-insensitive; the DB unique index is not, so every
# email crossing the API boundary is folded to lowercase here.
NormalizedEmail = Annotated[EmailStr, AfterValidator(str.lower)]

class UserCreate(BaseModel):
    email: NormalizedEmail
    # 72 is bcrypt's silent-truncation limit.
    password: str = Field(min_length=12, max_length=72)
    full_name: str
    role: Role

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: Role

    model_config = {"from_attributes": True}

import uuid
from pydantic import BaseModel, EmailStr

from app.models.user import Role

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: Role

    model_config = {"from_attributes": True}

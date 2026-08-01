import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.deps import get_current_user, require_role
from app.core.security import hash_password
from app.db import get_db
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserOut

router = APIRouter(tags=["users"])

@router.get("/users/me", response_model=UserOut)
def read_current_user(user: User = Depends(get_current_user)) -> User:
    return user

@router.post("/users", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.admin)),
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)
    return user

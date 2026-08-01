from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, verify_signature
from app.core.security import create_access_token, verify_password
from app.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignatureRequest, SignatureResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter_by(email=payload.email, is_active=True).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user_id=str(user.id), role=user.role)
    return TokenResponse(access_token=token)

@router.post("/verify-signature", response_model=SignatureResponse)
def verify_signature_endpoint(payload: SignatureRequest, user: User = Depends(get_current_user)) -> SignatureResponse:
    verify_signature(payload.password, user)
    return SignatureResponse(verified=True)

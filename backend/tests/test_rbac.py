import uuid
import pytest
from fastapi import HTTPException
from app.core.security import hash_password, create_access_token
from app.core.deps import require_role, verify_signature
from app.models.user import User, Role

def _make_user(db_session, role):
    user = User(
        id=uuid.uuid4(),
        email=f"{role}@example.com",
        password_hash=hash_password("pw"),
        full_name="Test User",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    return user

def test_me_endpoint_returns_current_user(client, db_session):
    user = _make_user(db_session, Role.coordinator)
    token = create_access_token(user_id=str(user.id), role=user.role)

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == user.email

def test_me_endpoint_rejects_missing_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_admin_only_route_rejects_non_admin(client, db_session):
    user = _make_user(db_session, Role.coordinator)
    token = create_access_token(user_id=str(user.id), role=user.role)

    response = client.post(
        "/users",
        json={"email": "new@example.com", "password": "correct-horse-battery", "full_name": "New Guy", "role": "approver"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

def test_admin_only_route_allows_admin(client, db_session):
    admin = _make_user(db_session, Role.admin)
    token = create_access_token(user_id=str(admin.id), role=admin.role)

    response = client.post(
        "/users",
        json={"email": "new@example.com", "password": "correct-horse-battery", "full_name": "New Guy", "role": "approver"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

def test_verify_signature_success(db_session):
    """verify_signature should not raise when password matches stored hash."""
    user = _make_user(db_session, Role.coordinator)
    # Should not raise
    verify_signature("pw", user)

def test_verify_signature_failure(db_session):
    """verify_signature should raise HTTPException with 401 when password does not match."""
    user = _make_user(db_session, Role.coordinator)
    with pytest.raises(HTTPException) as exc_info:
        verify_signature("wrong_password", user)
    assert exc_info.value.status_code == 401

def test_require_role_allows_any_of_multiple_roles_and_rejects_others(db_session):
    """require_role(*roles) is the variadic usage pattern later plans rely
    on (e.g. require_role(Role.approver, Role.admin)) - verify both listed
    roles are allowed and an unlisted role is rejected."""
    approver = _make_user(db_session, Role.approver)
    admin = _make_user(db_session, Role.admin)
    coordinator = _make_user(db_session, Role.coordinator)
    checker = require_role(Role.approver, Role.admin)

    assert checker(user=approver) is approver
    assert checker(user=admin) is admin
    with pytest.raises(HTTPException) as exc_info:
        checker(user=coordinator)
    assert exc_info.value.status_code == 403

def test_duplicate_email_returns_409(client, db_session):
    """POST /users with duplicate email should return 409."""
    admin = _make_user(db_session, Role.admin)
    token = create_access_token(user_id=str(admin.id), role=admin.role)

    # First request to create a user
    response1 = client.post(
        "/users",
        json={"email": "duplicate@example.com", "password": "correct-horse-battery", "full_name": "First User", "role": "approver"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response1.status_code == 201

    # Second request with same email should return 409
    response2 = client.post(
        "/users",
        json={"email": "duplicate@example.com", "password": "correct-horse-battery", "full_name": "Second User", "role": "coordinator"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"].lower()

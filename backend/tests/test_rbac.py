import uuid
from app.core.security import hash_password, create_access_token
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
        json={"email": "new@example.com", "password": "pw123456", "full_name": "New Guy", "role": "approver"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

def test_admin_only_route_allows_admin(client, db_session):
    admin = _make_user(db_session, Role.admin)
    token = create_access_token(user_id=str(admin.id), role=admin.role)

    response = client.post(
        "/users",
        json={"email": "new@example.com", "password": "pw123456", "full_name": "New Guy", "role": "approver"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

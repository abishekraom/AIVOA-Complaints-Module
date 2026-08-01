import uuid
from app.core.security import hash_password
from app.models.user import User, Role

def test_login_returns_jwt_for_valid_credentials(client, db_session):
    user = User(
        id=uuid.uuid4(),
        email="approver@example.com",
        password_hash=hash_password("correct-horse-battery"),
        full_name="Anita Rao",
        role=Role.approver,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/auth/login", json={"email": "approver@example.com", "password": "correct-horse-battery"})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

def test_login_rejects_wrong_password(client, db_session):
    user = User(
        id=uuid.uuid4(),
        email="coord@example.com",
        password_hash=hash_password("real-password"),
        full_name="K. Nair",
        role=Role.coordinator,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/auth/login", json={"email": "coord@example.com", "password": "wrong-password"})

    assert response.status_code == 401

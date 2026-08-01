import uuid
from app.core.security import hash_password, create_access_token
from app.models.user import Role, User


def test_verify_signature_accepts_correct_password(client, db_session):
    user = User(id=uuid.uuid4(), email="a@x.com", password_hash=hash_password("my-signature-pw"), full_name="Approver", role=Role.approver)
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user_id=str(user.id), role=user.role)

    response = client.post(
        "/auth/verify-signature",
        json={"password": "my-signature-pw"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"verified": True}


def test_verify_signature_rejects_wrong_password(client, db_session):
    user = User(id=uuid.uuid4(), email="b@x.com", password_hash=hash_password("real-pw"), full_name="Approver", role=Role.approver)
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user_id=str(user.id), role=user.role)

    response = client.post(
        "/auth/verify-signature",
        json={"password": "wrong-pw"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401

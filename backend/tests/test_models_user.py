import uuid
from app.models.user import User, Role

def test_user_defaults_to_active_and_stores_role(db_session):
    user = User(
        id=uuid.uuid4(),
        email="coordinator@example.com",
        password_hash="hashed",
        full_name="Priya Sharma",
        role=Role.coordinator,
    )
    db_session.add(user)
    db_session.commit()

    fetched = db_session.query(User).filter_by(email="coordinator@example.com").one()
    assert fetched.role == Role.coordinator
    assert fetched.is_active is True

def test_role_enum_has_exactly_three_values():
    assert {r.value for r in Role} == {"coordinator", "approver", "admin"}

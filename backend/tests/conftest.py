import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db import Base

TEST_DB_NAME = f"test_{uuid.uuid4().hex[:8]}"
ADMIN_URL = settings.database_url.rsplit("/", 1)[0] + "/postgres"
TEST_URL = settings.database_url.rsplit("/", 1)[0] + f"/{TEST_DB_NAME}"

@pytest.fixture(scope="session", autouse=True)
def _test_database():
    admin_engine = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    engine = create_engine(TEST_URL)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    from app.models import user, complaint, attachment, audit  # noqa: F401
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE {TEST_DB_NAME}"))
    admin_engine.dispose()

@pytest.fixture()
def db_session(_test_database):
    connection = _test_database.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import get_db

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

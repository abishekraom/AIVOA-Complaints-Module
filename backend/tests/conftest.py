import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
# JWT_SECRET is a required setting with no default, so the suite supplies its
# own throwaway value when the environment does not already provide one.
os.environ.setdefault("JWT_SECRET", "test-secret")

from app.config import settings

TEST_DB_NAME = f"test_{uuid.uuid4().hex[:8]}"
ADMIN_URL = settings.database_url.rsplit("/", 1)[0] + "/postgres"
TEST_URL = settings.database_url.rsplit("/", 1)[0] + f"/{TEST_DB_NAME}"

BACKEND_DIR = Path(__file__).resolve().parent.parent
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"

@pytest.fixture(scope="session", autouse=True)
def _test_database():
    host = make_url(settings.database_url).host or "localhost"
    if host not in ("localhost", "127.0.0.1", "::1"):
        pytest.exit(
            f"Refusing to run: DATABASE_URL points at host {host!r}. "
            "The test suite creates and drops databases, so it only runs "
            "against a local Postgres.",
            returncode=1,
        )
    admin_engine = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))

    # Run the real Alembic migration chain against the scratch database,
    # instead of Base.metadata.create_all(), so schema drift between the
    # models and the committed migrations is caught by the test suite.
    # The vector extension is created by migration 0001, so no manual
    # CREATE EXTENSION step is needed here.
    original_cwd = os.getcwd()
    os.chdir(BACKEND_DIR)
    try:
        alembic_cfg = Config(str(ALEMBIC_INI))
        alembic_cfg.set_main_option("sqlalchemy.url", TEST_URL)
        command.upgrade(alembic_cfg, "head")
    finally:
        os.chdir(original_cwd)

    engine = create_engine(TEST_URL)
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

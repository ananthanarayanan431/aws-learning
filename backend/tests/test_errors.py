"""Every endpoint must turn database failures into the JSON error envelope, never a raw 500."""

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.database import get_db
from app.main import app

API = "/api/v1"


class FailingSession:
    """Stands in for AsyncSession; every DB call raises `exc`."""

    def __init__(self, exc: Exception):
        self.exc = exc
        self.rolled_back = False

    async def _fail(self, *_, **__):
        raise self.exc

    get = execute = scalars = commit = refresh = delete = _fail

    def add(self, *_):
        pass

    async def rollback(self):
        self.rolled_back = True


def use_failing_db(exc: Exception) -> FailingSession:
    session = FailingSession(exc)

    async def override():
        yield session

    app.dependency_overrides[get_db] = override
    return session


ENDPOINTS = [
    ("get", "/tasks", None),
    ("post", "/tasks", {"title": "x"}),
    ("get", "/tasks/1", None),
    ("patch", "/tasks/1", {"title": "y"}),
    ("delete", "/tasks/1", None),
    ("get", "/today", None),
    ("post", "/today/carry-over", None),
    ("get", "/categories", None),
    ("post", "/categories", {"name": "c"}),
    ("delete", "/categories/1", None),
    ("get", "/tags", None),
    ("post", "/tags", {"name": "t"}),
    ("delete", "/tags/1", None),
]


@pytest.mark.parametrize(("method", "path", "body"), ENDPOINTS)
async def test_connection_failure_returns_503(client, method, path, body):
    session = use_failing_db(OperationalError("SELECT 1", {}, Exception("connection refused")))
    r = await client.request(method, API + path, json=body)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "connection refused" not in r.text  # internals must not leak
    assert session.rolled_back


@pytest.mark.parametrize(("method", "path", "body"), ENDPOINTS)
async def test_unreachable_server_os_error_returns_503(client, method, path, body):
    use_failing_db(ConnectionRefusedError(61, "Connection refused"))
    r = await client.request(method, API + path, json=body)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "DATABASE_UNAVAILABLE"


@pytest.mark.parametrize(("method", "path", "body"), ENDPOINTS)
async def test_generic_database_error_returns_500(client, method, path, body):
    use_failing_db(SQLAlchemyError("boom"))
    r = await client.request(method, API + path, json=body)
    assert r.status_code == 500
    assert r.json()["success"] is False
    assert r.json()["error"]["code"] == "DATABASE_ERROR"
    assert "boom" not in r.text


async def test_task_integrity_error_returns_409(client):
    session = use_failing_db(IntegrityError("INSERT", {}, Exception("fk violation")))
    r = await client.post(f"{API}/tasks", json={"title": "x"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"
    assert session.rolled_back

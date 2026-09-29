from datetime import date, timedelta

from app.database import get_db
from app.main import app

API = "/api/v1"


def make_task(client, **body):
    body.setdefault("title", "t")
    r = client.post(f"{API}/tasks", json=body)
    assert r.status_code == 201, r.text
    return r.json()["data"]


def test_backend_health(client):
    r = client.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["data"] == {"status": "ok", "service": "backend"}


def test_db_health_ok(client):
    r = client.get(f"{API}/health/db")
    assert r.status_code == 200
    assert r.json()["data"]["service"] == "database"


def test_db_health_down_returns_error_envelope(client):
    class Broken:
        def execute(self, *_):
            raise RuntimeError("boom")

    app.dependency_overrides[get_db] = lambda: Broken()
    r = client.get(f"{API}/health/db")
    assert r.status_code == 503
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"


def test_create_and_get_task(client):
    t = make_task(client, title="Write report", priority="high")
    r = client.get(f"{API}/tasks/{t['id']}")
    assert r.json() == {
        "success": True,
        "message": "OK",
        "data": t,
        "meta": None,
    }
    assert t["priority"] == "high" and t["status"] == "todo"


def test_validation_error_envelope(client):
    r = client.post(f"{API}/tasks", json={"title": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"][0]["field"] == "title"


def test_not_found_envelope(client):
    r = client.get(f"{API}/tasks/999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_unknown_route_uses_error_envelope(client):
    r = client.get(f"{API}/nope")
    assert r.status_code == 404
    assert r.json()["success"] is False


def test_completing_sets_completed_at(client):
    t = make_task(client)
    done = client.patch(f"{API}/tasks/{t['id']}", json={"status": "done"}).json()["data"]
    assert done["completed_at"] is not None
    undone = client.patch(f"{API}/tasks/{t['id']}", json={"status": "todo"}).json()["data"]
    assert undone["completed_at"] is None


def test_patch_can_clear_nullable_field(client):
    t = make_task(client, due_date="2030-01-01")
    r = client.patch(f"{API}/tasks/{t['id']}", json={"due_date": None})
    assert r.json()["data"]["due_date"] is None


def test_subtasks_nest_one_level(client):
    parent = make_task(client, title="parent")
    child = make_task(client, title="child", parent_id=parent["id"])
    r = client.post(f"{API}/tasks", json={"title": "x", "parent_id": child["id"]})
    assert r.status_code == 400
    listed = client.get(f"{API}/tasks").json()["data"]
    assert len(listed) == 1 and listed[0]["subtasks"][0]["id"] == child["id"]


def test_categories_tags_and_filters(client):
    cat = client.post(f"{API}/categories", json={"name": "Work"}).json()["data"]
    dup = client.post(f"{API}/categories", json={"name": "Work"})
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "CONFLICT"
    tag = client.post(f"{API}/tags", json={"name": "deep"}).json()["data"]
    make_task(client, title="a", category_id=cat["id"], tag_ids=[tag["id"]])
    make_task(client, title="b")
    assert len(client.get(f"{API}/tasks", params={"category_id": cat["id"]}).json()["data"]) == 1
    assert len(client.get(f"{API}/tasks", params={"tag_id": tag["id"]}).json()["data"]) == 1
    bad = client.post(f"{API}/tasks", json={"title": "x", "tag_ids": [999]})
    assert bad.status_code == 400


def test_today_view_and_carry_over(client):
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    make_task(client, title="today", planned_date=today.isoformat())
    make_task(client, title="late", planned_date=yesterday)
    make_task(client, title="late-done", planned_date=yesterday, status="done")
    make_task(client, title="future", planned_date=(today + timedelta(days=3)).isoformat())

    titles = {t["title"] for t in client.get(f"{API}/today").json()["data"]}
    assert titles == {"today", "late"}

    r = client.post(f"{API}/today/carry-over")
    assert r.json()["data"]["moved"] == 1
    planned = client.get(f"{API}/tasks", params={"planned_date": today.isoformat()}).json()["data"]
    assert {t["title"] for t in planned} == {"today", "late"}

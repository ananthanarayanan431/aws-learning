from datetime import date, timedelta

from app.database import get_db
from app.main import app

API = "/api/v1"


async def make_task(client, **body):
    body.setdefault("title", "t")
    r = await client.post(f"{API}/tasks", json=body)
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def test_backend_health(client):
    r = await client.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["data"] == {"status": "ok", "service": "backend"}


async def test_db_health_ok(client):
    r = await client.get(f"{API}/health/db")
    assert r.status_code == 200
    assert r.json()["data"]["service"] == "database"


async def test_db_health_down_returns_error_envelope(client):
    class Broken:
        async def execute(self, *_):
            raise RuntimeError("boom")

    async def broken_db():
        yield Broken()

    app.dependency_overrides[get_db] = broken_db
    r = await client.get(f"{API}/health/db")
    assert r.status_code == 503
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"


async def test_create_and_get_task(client):
    t = await make_task(client, title="Write report", priority="high")
    r = await client.get(f"{API}/tasks/{t['id']}")
    assert r.json() == {
        "success": True,
        "message": "OK",
        "data": t,
        "meta": None,
    }
    assert t["priority"] == "high" and t["status"] == "todo"


async def test_validation_error_envelope(client):
    r = await client.post(f"{API}/tasks", json={"title": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"][0]["field"] == "title"


async def test_not_found_envelope(client):
    r = await client.get(f"{API}/tasks/999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


async def test_unknown_route_uses_error_envelope(client):
    r = await client.get(f"{API}/nope")
    assert r.status_code == 404
    assert r.json()["success"] is False


async def test_completing_sets_completed_at(client):
    t = await make_task(client)
    done = (await client.patch(f"{API}/tasks/{t['id']}", json={"status": "done"})).json()["data"]
    assert done["completed_at"] is not None
    undone = (await client.patch(f"{API}/tasks/{t['id']}", json={"status": "todo"})).json()["data"]
    assert undone["completed_at"] is None


async def test_patch_can_clear_nullable_field(client):
    t = await make_task(client, due_date="2030-01-01")
    r = await client.patch(f"{API}/tasks/{t['id']}", json={"due_date": None})
    assert r.json()["data"]["due_date"] is None


async def test_subtasks_nest_one_level(client):
    parent = await make_task(client, title="parent")
    child = await make_task(client, title="child", parent_id=parent["id"])
    r = await client.post(f"{API}/tasks", json={"title": "x", "parent_id": child["id"]})
    assert r.status_code == 400
    listed = (await client.get(f"{API}/tasks")).json()["data"]
    assert len(listed) == 1 and listed[0]["subtasks"][0]["id"] == child["id"]


async def test_categories_tags_and_filters(client):
    cat = (await client.post(f"{API}/categories", json={"name": "Work"})).json()["data"]
    dup = await client.post(f"{API}/categories", json={"name": "Work"})
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "CONFLICT"
    tag = (await client.post(f"{API}/tags", json={"name": "deep"})).json()["data"]
    (await make_task(client, title="a", category_id=cat["id"], tag_ids=[tag["id"]]))
    (await make_task(client, title="b"))
    assert (
        len((await client.get(f"{API}/tasks", params={"category_id": cat["id"]})).json()["data"])
        == 1
    )
    assert len((await client.get(f"{API}/tasks", params={"tag_id": tag["id"]})).json()["data"]) == 1
    bad = await client.post(f"{API}/tasks", json={"title": "x", "tag_ids": [999]})
    assert bad.status_code == 400


async def test_today_view_and_carry_over(client):
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    (await make_task(client, title="today", planned_date=today.isoformat()))
    (await make_task(client, title="late", planned_date=yesterday))
    (await make_task(client, title="late-done", planned_date=yesterday, status="done"))
    (await make_task(client, title="future", planned_date=(today + timedelta(days=3)).isoformat()))

    titles = {t["title"] for t in (await client.get(f"{API}/today")).json()["data"]}
    assert titles == {"today", "late"}

    r = await client.post(f"{API}/today/carry-over")
    assert r.json()["data"]["moved"] == 1
    planned = (await client.get(f"{API}/tasks", params={"planned_date": today.isoformat()})).json()[
        "data"
    ]
    assert {t["title"] for t in planned} == {"today", "late"}


async def test_request_id_is_generated_and_echoed(client):
    r = await client.get(f"{API}/health")
    assert r.headers["x-request-id"]
    r = await client.get(f"{API}/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["x-request-id"] == "abc123"


async def test_date_range_filter_uses_planned_then_due_date(client):
    await make_task(client, title="planned", planned_date="2030-05-10")
    await make_task(client, title="due-only", due_date="2030-05-20")
    await make_task(client, title="planned-wins", planned_date="2030-06-02", due_date="2030-05-15")
    await make_task(client, title="undated")

    async def titles(**params):
        r = await client.get(f"{API}/tasks", params=params)
        return {t["title"] for t in r.json()["data"]}

    assert await titles(date_from="2030-05-01", date_to="2030-05-31") == {"planned", "due-only"}
    assert await titles(date_from="2030-06-01", date_to="2030-06-30") == {"planned-wins"}
    assert await titles(date_from="2030-05-11") == {"due-only", "planned-wins"}

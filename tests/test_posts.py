"""
Integration tests for the Post CRUD endpoints — test plan item 1c.

Covers:
  - Create a post (201)
  - List posts for the authenticated user
  - Get a specific post by ID
  - Update a post (PATCH)
  - Delete a post (204) and confirm 404 on re-fetch
  - Post isolation: User B cannot read or modify User A's posts
  - Auth guard: all endpoints require a valid token
"""
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient

# A fixed future timestamp used for scheduled_time in all tests.
# Must be timezone-aware; the API accepts ISO 8601 strings.
FUTURE = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _login(client: AsyncClient, username: str, password: str = "pass123") -> str:
    """Register + login and return the access token."""
    await client.post(
        "/register",
        json={"email": f"{username}@test.com", "username": username, "password": password},
    )
    resp = await client.post("/token", data={"username": username, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_post(client: AsyncClient, token: str, content: str = "Test post") -> dict:
    resp = await client.post(
        "/posts/",
        json={"content": content, "scheduled_time": FUTURE, "platform": "tiktok"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# 1c — Post CRUD
# ---------------------------------------------------------------------------

async def test_create_post_returns_201_with_correct_fields(client: AsyncClient):
    token = await _login(client, "creator")
    resp = await client.post(
        "/posts/",
        json={"content": "My first TikTok post", "scheduled_time": FUTURE, "platform": "tiktok"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "My first TikTok post"
    assert data["platform"] == "tiktok"
    assert data["status"] == "scheduled"
    assert "id" in data
    assert "created_at" in data


async def test_list_posts_returns_only_current_users_posts(client: AsyncClient):
    token = await _login(client, "lister")
    await _create_post(client, token, "Post one")
    await _create_post(client, token, "Post two")

    resp = await client.get("/posts/", headers=_auth(token))
    assert resp.status_code == 200
    posts = resp.json()
    assert len(posts) == 2
    contents = {p["content"] for p in posts}
    assert contents == {"Post one", "Post two"}


async def test_get_post_by_id(client: AsyncClient):
    token = await _login(client, "getter")
    post = await _create_post(client, token, "Fetch this post")

    resp = await client.get(f"/posts/{post['id']}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["content"] == "Fetch this post"


async def test_update_post_content(client: AsyncClient):
    token = await _login(client, "updater")
    post = await _create_post(client, token, "Original content")

    resp = await client.patch(
        f"/posts/{post['id']}",
        json={"content": "Updated content"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated content"


async def test_update_post_scheduled_time(client: AsyncClient):
    token = await _login(client, "rescheduler")
    post = await _create_post(client, token)

    new_time = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = await client.patch(
        f"/posts/{post['id']}",
        json={"scheduled_time": new_time},
        headers=_auth(token),
    )
    assert resp.status_code == 200


async def test_delete_post_returns_204_then_404(client: AsyncClient):
    token = await _login(client, "deleter")
    post = await _create_post(client, token, "Delete me")

    # Delete
    resp = await client.delete(f"/posts/{post['id']}", headers=_auth(token))
    assert resp.status_code == 204

    # Subsequent fetch must return 404
    resp = await client.get(f"/posts/{post['id']}", headers=_auth(token))
    assert resp.status_code == 404


async def test_get_nonexistent_post_returns_404(client: AsyncClient):
    token = await _login(client, "miss_user")
    resp = await client.get("/posts/99999", headers=_auth(token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Post isolation — User B cannot access User A's posts
# ---------------------------------------------------------------------------

async def test_user_cannot_read_another_users_post(client: AsyncClient):
    token_a = await _login(client, "owner_a")
    token_b = await _login(client, "intruder_b")

    post = await _create_post(client, token_a, "Private post")

    resp = await client.get(f"/posts/{post['id']}", headers=_auth(token_b))
    assert resp.status_code == 404  # 404 not 403 — we don't leak existence


async def test_user_cannot_update_another_users_post(client: AsyncClient):
    token_a = await _login(client, "owner_c")
    token_b = await _login(client, "intruder_d")

    post = await _create_post(client, token_a)

    resp = await client.patch(
        f"/posts/{post['id']}",
        json={"content": "Hijacked"},
        headers=_auth(token_b),
    )
    assert resp.status_code == 404


async def test_user_cannot_delete_another_users_post(client: AsyncClient):
    token_a = await _login(client, "owner_e")
    token_b = await _login(client, "intruder_f")

    post = await _create_post(client, token_a)

    resp = await client.delete(f"/posts/{post['id']}", headers=_auth(token_b))
    assert resp.status_code == 404


async def test_list_posts_does_not_include_other_users_posts(client: AsyncClient):
    token_a = await _login(client, "list_owner")
    token_b = await _login(client, "list_intruder")

    await _create_post(client, token_a, "Owner's post")

    # User B's list must be empty
    resp = await client.get("/posts/", headers=_auth(token_b))
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Auth guards
# ---------------------------------------------------------------------------

async def test_create_post_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/posts/",
        json={"content": "No auth", "scheduled_time": FUTURE},
    )
    assert resp.status_code == 401


async def test_list_posts_requires_auth(client: AsyncClient):
    resp = await client.get("/posts/")
    assert resp.status_code == 401


async def test_get_post_requires_auth(client: AsyncClient):
    resp = await client.get("/posts/1")
    assert resp.status_code == 401

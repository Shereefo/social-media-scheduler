"""
Integration tests for the authentication system — Phase 5 identity upgrades.

Covers:
  1a. Full auth flow: register → login → /users/me → logout → token rejection
      → refresh token rotation → replay attack rejection
  1b. Token version revocation: logout invalidates all outstanding access tokens
      and the stored refresh token
  1d. Admin role guard: regular users receive 403, unauthenticated users 401
"""
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register_and_login(
    client: AsyncClient,
    username: str,
    password: str = "strongpass123",
) -> dict:
    """Register a new user and return the full login token response."""
    await client.post(
        "/register",
        json={
            "email": f"{username}@test.com",
            "username": username,
            "password": password,
        },
    )
    resp = await client.post(
        "/token", data={"username": username, "password": password}
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1a — Full auth flow
# ---------------------------------------------------------------------------

async def test_register_returns_user_without_sensitive_fields(client: AsyncClient):
    resp = await client.post(
        "/register",
        json={"email": "alice@test.com", "username": "alice", "password": "pass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@test.com"
    # These must never appear in any API response
    assert "hashed_password" not in data
    assert "tiktok_access_token" not in data
    assert "refresh_token_hash" not in data


async def test_login_returns_access_and_refresh_token(client: AsyncClient):
    tokens = await _register_and_login(client, "bob")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    # Both tokens should be non-empty strings
    assert len(tokens["access_token"]) > 0
    assert len(tokens["refresh_token"]) > 0


async def test_users_me_with_valid_token(client: AsyncClient):
    tokens = await _register_and_login(client, "carol")
    resp = await client.get("/users/me", headers=_auth(tokens["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["username"] == "carol"


async def test_users_me_without_token_is_401(client: AsyncClient):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


async def test_logout_invalidates_access_token(client: AsyncClient):
    tokens = await _register_and_login(client, "dave")
    headers = _auth(tokens["access_token"])

    # Token works before logout
    assert (await client.get("/users/me", headers=headers)).status_code == 200

    # Logout
    assert (await client.post("/auth/logout", headers=headers)).status_code == 204

    # Same access token must now be rejected
    assert (await client.get("/users/me", headers=headers)).status_code == 401


async def test_refresh_token_rotation_issues_new_token_pair(client: AsyncClient):
    tokens = await _register_and_login(client, "eve")
    original_access = tokens["access_token"]
    original_refresh = tokens["refresh_token"]

    resp = await client.post(
        "/auth/refresh", json={"refresh_token": original_refresh}
    )
    assert resp.status_code == 200
    new_tokens = resp.json()

    # New tokens must differ from originals
    assert new_tokens["access_token"] != original_access
    assert new_tokens["refresh_token"] != original_refresh

    # New access token must work
    resp = await client.get(
        "/users/me", headers=_auth(new_tokens["access_token"])
    )
    assert resp.status_code == 200


async def test_replay_attack_refresh_token_rejected(client: AsyncClient):
    """
    After a refresh token is used once (rotated), presenting the same token
    again must return 401. This prevents a stolen refresh token from being
    replayed after it has already been consumed.
    """
    tokens = await _register_and_login(client, "frank")
    original_refresh = tokens["refresh_token"]

    # First use — valid
    resp = await client.post(
        "/auth/refresh", json={"refresh_token": original_refresh}
    )
    assert resp.status_code == 200

    # Second use (replay) — must be rejected
    resp = await client.post(
        "/auth/refresh", json={"refresh_token": original_refresh}
    )
    assert resp.status_code == 401


async def test_wrong_password_login_rejected(client: AsyncClient):
    await client.post(
        "/register",
        json={"email": "grace@test.com", "username": "grace", "password": "correct"},
    )
    resp = await client.post(
        "/token", data={"username": "grace", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_duplicate_registration_rejected(client: AsyncClient):
    payload = {"email": "henry@test.com", "username": "henry", "password": "pass"}
    await client.post("/register", json=payload)
    resp = await client.post("/register", json=payload)
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 1b — Token version revocation
# ---------------------------------------------------------------------------

async def test_logout_bumps_token_version_invalidating_all_access_tokens(
    client: AsyncClient,
):
    """
    token_version is embedded in the JWT at login time. Logout increments the
    DB value, so every outstanding JWT with the old version fails the check
    in get_current_user — no blocklist table needed.
    """
    tokens = await _register_and_login(client, "ivan")
    old_access = tokens["access_token"]
    old_refresh = tokens["refresh_token"]
    headers = _auth(old_access)

    # Logout bumps token_version
    await client.post("/auth/logout", headers=headers)

    # Old access token is now stale (version mismatch)
    assert (await client.get("/users/me", headers=headers)).status_code == 401

    # Old refresh token hash was also cleared — cannot be used for a new access token
    resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 401


async def test_new_login_after_logout_produces_valid_token(client: AsyncClient):
    """
    After logout a fresh login must succeed with the new token_version.
    """
    tokens = await _register_and_login(client, "julia")
    await client.post("/auth/logout", headers=_auth(tokens["access_token"]))

    # New login
    new_tokens = await _register_and_login(client, "julia")
    resp = await client.get(
        "/users/me", headers=_auth(new_tokens["access_token"])
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 1d — Admin role guard
# ---------------------------------------------------------------------------

async def test_regular_user_gets_403_on_admin_endpoint(client: AsyncClient):
    tokens = await _register_and_login(client, "karen")
    resp = await client.get(
        "/test/admin-only", headers=_auth(tokens["access_token"])
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin privileges required"


async def test_unauthenticated_request_to_admin_endpoint_is_401(client: AsyncClient):
    resp = await client.get("/test/admin-only")
    assert resp.status_code == 401


async def test_admin_role_user_can_access_admin_endpoint(
    client: AsyncClient, db_session
):
    """
    Promote a user to admin directly in the DB (simulating an admin setup
    script or seed) and confirm the endpoint returns 200.
    """
    from backend.models import User, UserRole
    from backend.auth import get_password_hash

    # Create user with admin role directly via DB session
    admin_user = User(
        email="admin@test.com",
        username="adminuser",
        hashed_password=get_password_hash("adminpass"),
        role=UserRole.admin,
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    # Login
    resp = await client.post(
        "/token", data={"username": "adminuser", "password": "adminpass"}
    )
    assert resp.status_code == 200
    tokens = resp.json()

    # Admin endpoint should return 200
    resp = await client.get(
        "/test/admin-only", headers=_auth(tokens["access_token"])
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "adminuser"

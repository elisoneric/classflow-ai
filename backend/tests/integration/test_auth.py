async def test_login_returns_access_token_and_refresh_cookie(client, course_rep_user):
    email, password = course_rep_user
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in client.cookies


async def test_login_rejects_wrong_password(client, course_rep_user):
    email, _ = course_rep_user
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
    assert response.status_code == 401


async def test_refresh_issues_new_access_token(client, course_rep_user):
    email, password = course_rep_user
    await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_protected_endpoint_requires_auth(client):
    response = await client.get("/api/v1/courses")
    assert response.status_code in (401, 403)

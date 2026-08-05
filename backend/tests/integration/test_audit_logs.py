async def test_course_creation_is_audited(client, auth_headers):
    r = await client.post(
        "/api/v1/semesters", headers=auth_headers,
        json={"name": "Audit Test Semester", "start_date": "2026-01-12", "end_date": "2026-05-15"},
    )
    semester_id = r.json()["id"]
    r = await client.post(
        "/api/v1/courses", headers=auth_headers,
        json={
            "semester_id": semester_id, "code": "CSC803", "title": "Algorithms",
            "announcement_email": "a@b.com",
        },
    )
    course_id = r.json()["id"]

    r = await client.get(
        "/api/v1/audit-logs", headers=auth_headers,
        params={"entity_type": "COURSE", "entity_id": course_id},
    )
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) == 1
    assert logs[0]["action"] == "COURSE_CREATED"
    assert logs[0]["actor"] == "COURSE_REP"


async def test_audit_logs_require_auth(client):
    r = await client.get("/api/v1/audit-logs")
    assert r.status_code in (401, 403)

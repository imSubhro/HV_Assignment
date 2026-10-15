from datetime import datetime, timedelta, timezone

from tests.conftest import auth_header, login


def future_iso(days: int = 10) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def past_iso(days: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _create(client, admin_token, **overrides):
    payload = {
        "title": "Probe conversation title",
        "description": "A sufficiently long description for the probe.",
        "scheduled_at": future_iso(),
        "duration_minutes": 45,
        "mode": "online",
        "location_or_link": "https://meet.example.com/probe",
        "capacity": 50,
        "cover_image_url": None,
        "speakers": [],
    }
    payload.update(overrides)
    r = client.post(
        "/api/v1/admin/conversations", json=payload, headers=auth_header(admin_token)
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_probe_patch_null_title(client, admin_token):
    cid = _create(client, admin_token)
    r = client.patch(
        f"/api/v1/admin/conversations/{cid}",
        json={"title": None},
        headers=auth_header(admin_token),
    )
    print("PATCH title=null ->", r.status_code, r.text)
    assert r.status_code == 200, f"got {r.status_code}: {r.text}"


def test_probe_patch_published_to_past(client, admin_token):
    cid = _create(client, admin_token, scheduled_at=future_iso(2))
    r = client.post(
        f"/api/v1/admin/conversations/{cid}/publish", headers=auth_header(admin_token)
    )
    assert r.status_code == 200, r.text
    r = client.patch(
        f"/api/v1/admin/conversations/{cid}",
        json={"scheduled_at": past_iso()},
        headers=auth_header(admin_token),
    )
    print("PATCH published->past ->", r.status_code, r.text)
    assert r.status_code == 200, f"got {r.status_code}: {r.text}"

from datetime import datetime, timedelta, timezone

from tests.conftest import auth_header


def future_iso(days: int = 10, hours: int = 0) -> str:
    moment = datetime.now(timezone.utc) + timedelta(days=days, hours=hours)
    return moment.isoformat().replace("+00:00", "Z")


def past_iso(days: int = 10) -> str:
    moment = datetime.now(timezone.utc) - timedelta(days=days)
    return moment.isoformat().replace("+00:00", "Z")


def conversation_payload(**overrides) -> dict:
    payload = {
        "title": "Founders & Funding: Early-Stage Lessons",
        "description": "An open conversation on raising the first round of capital.",
        "scheduled_at": future_iso(),
        "duration_minutes": 90,
        "mode": "online",
        "location_or_link": "https://meet.example.com/abc",
        "capacity": 100,
        "cover_image_url": None,
        "speakers": [
            {
                "name": "Rohan Mehta",
                "designation": "Partner, XYZ Ventures",
                "bio": "Investor in 30+ early-stage startups.",
                "photo_url": None,
            }
        ],
    }
    payload.update(overrides)
    return payload


def create_conversation(client, admin_token, **overrides) -> dict:
    response = client.post(
        "/api/v1/admin/conversations",
        json=conversation_payload(**overrides),
        headers=auth_header(admin_token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def backdate(client, admin_token, conversation_id: str, days: int = 10) -> dict:
    """Move a conversation's schedule into the past (allowed unless cancelled)."""
    response = client.patch(
        f"/api/v1/admin/conversations/{conversation_id}",
        json={"scheduled_at": past_iso(days)},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_new_conversation_is_draft_and_invisible_publicly(client, admin_token):
    created = create_conversation(client, admin_token)
    assert created["status"] == "draft"
    assert created["speakers"][0]["display_order"] == 0

    public_list = client.get("/api/v1/conversations").json()
    assert public_list["total_items"] == 0

    detail = client.get(f"/api/v1/conversations/{created['id']}")
    assert detail.status_code == 404


def test_publish_then_appears_in_upcoming(client, admin_token):
    created = create_conversation(client, admin_token)

    published = client.post(
        f"/api/v1/admin/conversations/{created['id']}/publish",
        headers=auth_header(admin_token),
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    listing = client.get("/api/v1/conversations?when=upcoming").json()
    assert listing["total_items"] == 1
    assert listing["items"][0]["id"] == created["id"]
    assert listing["items"][0]["speakers"][0]["name"] == "Rohan Mehta"


def test_past_published_conversation_appears_under_past(client, admin_token):
    created = create_conversation(client, admin_token)
    assert client.post(
        f"/api/v1/admin/conversations/{created['id']}/publish",
        headers=auth_header(admin_token),
    ).status_code == 200
    backdate(client, admin_token, created["id"])

    upcoming = client.get("/api/v1/conversations?when=upcoming").json()
    past = client.get("/api/v1/conversations?when=past").json()
    assert upcoming["total_items"] == 0
    assert past["total_items"] == 1
    assert past["items"][0]["id"] == created["id"]


def test_publish_with_past_schedule_returns_400(client, admin_token):
    created = create_conversation(client, admin_token)
    backdate(client, admin_token, created["id"])
    response = client.post(
        f"/api/v1/admin/conversations/{created['id']}/publish",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_cancelled_conversation_cannot_be_published_or_rescheduled(client, admin_token):
    created = create_conversation(client, admin_token)

    cancelled = client.post(
        f"/api/v1/admin/conversations/{created['id']}/cancel",
        headers=auth_header(admin_token),
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    publish = client.post(
        f"/api/v1/admin/conversations/{created['id']}/publish",
        headers=auth_header(admin_token),
    )
    assert publish.status_code == 400

    reschedule = client.patch(
        f"/api/v1/admin/conversations/{created['id']}",
        json={"scheduled_at": future_iso(20)},
        headers=auth_header(admin_token),
    )
    assert reschedule.status_code == 400


def test_unpublish_returns_to_draft(client, admin_token):
    created = create_conversation(client, admin_token)
    client.post(
        f"/api/v1/admin/conversations/{created['id']}/publish",
        headers=auth_header(admin_token),
    )
    response = client.post(
        f"/api/v1/admin/conversations/{created['id']}/unpublish",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "draft"
    assert client.get(f"/api/v1/conversations/{created['id']}").status_code == 404


def test_updating_speakers_replaces_list_but_omitting_keeps_it(client, admin_token):
    created = create_conversation(client, admin_token)
    conversation_id = created["id"]

    replaced = client.patch(
        f"/api/v1/admin/conversations/{conversation_id}",
        json={
            "speakers": [
                {"name": "Meera Iyer", "designation": "Founder"},
                {"name": "Arjun Rao", "designation": " angel investor"},
            ]
        },
        headers=auth_header(admin_token),
    )
    assert replaced.status_code == 200, replaced.text
    speakers = replaced.json()["speakers"]
    assert [s["name"] for s in speakers] == ["Meera Iyer", "Arjun Rao"]
    assert [s["display_order"] for s in speakers] == [0, 1]

    untouched = client.patch(
        f"/api/v1/admin/conversations/{conversation_id}",
        json={"duration_minutes": 60},
        headers=auth_header(admin_token),
    )
    assert untouched.status_code == 200
    assert [s["name"] for s in untouched.json()["speakers"]] == [
        "Meera Iyer",
        "Arjun Rao",
    ]
    assert untouched.json()["duration_minutes"] == 60

    emptied = client.patch(
        f"/api/v1/admin/conversations/{conversation_id}",
        json={"speakers": []},
        headers=auth_header(admin_token),
    )
    assert emptied.status_code == 200
    assert emptied.json()["speakers"] == []


def test_admin_cannot_change_status_via_patch(client, admin_token):
    created = create_conversation(client, admin_token)
    response = client.patch(
        f"/api/v1/admin/conversations/{created['id']}",
        json={"status": "published"},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "draft"


def test_normal_user_cannot_use_admin_conversation_routes(client, admin_token, user_token):
    created = create_conversation(client, admin_token)
    headers = auth_header(user_token)

    assert client.get("/api/v1/admin/conversations", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/v1/admin/conversations", json=conversation_payload(), headers=headers
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/admin/conversations/{created['id']}", headers=headers
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/admin/conversations/{created['id']}/publish", headers=headers
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/v1/admin/conversations/{created['id']}", headers=headers
        ).status_code
        == 403
    )


def test_delete_removes_conversation_and_speakers(client, admin_token, db):
    from app.models.conversation import ConversationSpeaker

    created = create_conversation(client, admin_token)
    conversation_id = created["id"]

    response = client.delete(
        f"/api/v1/admin/conversations/{conversation_id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 204
    assert (
        client.get(
            f"/api/v1/admin/conversations/{conversation_id}",
            headers=auth_header(admin_token),
        ).status_code
        == 404
    )
    assert (
        db.query(ConversationSpeaker)
        .filter(ConversationSpeaker.conversation_id == conversation_id)
        .count()
        == 0
    )


def test_admin_list_filters_and_public_filters(client, admin_token):
    online = create_conversation(
        client, admin_token, title="Online Talk Alpha", mode="online",
        location_or_link="https://meet.example.com/alpha",
    )
    offline = create_conversation(
        client, admin_token, title="Offline Meetup Beta", mode="offline",
        location_or_link="Bangalore, India",
        scheduled_at=future_iso(3),
    )
    client.post(
        f"/api/v1/admin/conversations/{online['id']}/publish",
        headers=auth_header(admin_token),
    )
    client.post(
        f"/api/v1/admin/conversations/{offline['id']}/publish",
        headers=auth_header(admin_token),
    )

    drafts = client.get(
        "/api/v1/admin/conversations?status=draft", headers=auth_header(admin_token)
    ).json()
    assert drafts["total_items"] == 0

    by_status = client.get(
        "/api/v1/admin/conversations?status=published&when=upcoming",
        headers=auth_header(admin_token),
    ).json()
    assert by_status["total_items"] == 2

    searched = client.get(
        "/api/v1/admin/conversations?search=alpha",
        headers=auth_header(admin_token),
    ).json()
    assert searched["total_items"] == 1
    assert searched["items"][0]["id"] == online["id"]

    public_offline = client.get("/api/v1/conversations?mode=offline").json()
    assert public_offline["total_items"] == 1
    assert public_offline["items"][0]["id"] == offline["id"]

    public_search = client.get("/api/v1/conversations?search=ALPHA").json()
    assert public_search["total_items"] == 1


def test_conversation_validation_rules(client, admin_token):
    headers = auth_header(admin_token)

    bad_title = client.post(
        "/api/v1/admin/conversations",
        json=conversation_payload(title="ab"),
        headers=headers,
    )
    assert bad_title.status_code == 422

    bad_duration = client.post(
        "/api/v1/admin/conversations",
        json=conversation_payload(duration_minutes=5),
        headers=headers,
    )
    assert bad_duration.status_code == 422

    bad_online_link = client.post(
        "/api/v1/admin/conversations",
        json=conversation_payload(location_or_link="not a url"),
        headers=headers,
    )
    assert bad_online_link.status_code == 422
    assert any(
        detail["field"] == "location_or_link"
        for detail in bad_online_link.json()["error"]["details"]
    )

    past_schedule = client.post(
        "/api/v1/admin/conversations",
        json=conversation_payload(scheduled_at=past_iso()),
        headers=headers,
    )
    assert past_schedule.status_code == 400

    too_many_speakers = client.post(
        "/api/v1/admin/conversations",
        json=conversation_payload(
            speakers=[{"name": f"Speaker {index}"} for index in range(11)]
        ),
        headers=headers,
    )
    assert too_many_speakers.status_code == 422


def test_pagination_shape_on_public_list(client, admin_token):
    for index in range(3):
        created = create_conversation(
            client, admin_token, title=f"Conversation number {index}"
        )
        client.post(
            f"/api/v1/admin/conversations/{created['id']}/publish",
            headers=auth_header(admin_token),
        )

    response = client.get("/api/v1/conversations?page=1&page_size=2")
    body = response.json()
    assert response.status_code == 200
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total_items"] == 3
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2

    invalid = client.get("/api/v1/conversations?page=0")
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_upcoming_sorted_ascending_and_past_descending(client, admin_token):
    soon = create_conversation(
        client, admin_token, title="Soon", scheduled_at=future_iso(1)
    )
    later = create_conversation(
        client, admin_token, title="Later", scheduled_at=future_iso(30)
    )
    older = create_conversation(
        client, admin_token, title="Older", scheduled_at=future_iso(40)
    )
    recent = create_conversation(
        client, admin_token, title="Recent", scheduled_at=future_iso(50)
    )
    for conversation in (soon, later, older, recent):
        client.post(
            f"/api/v1/admin/conversations/{conversation['id']}/publish",
            headers=auth_header(admin_token),
        )
    backdate(client, admin_token, older["id"], days=30)
    backdate(client, admin_token, recent["id"], days=1)

    upcoming = client.get("/api/v1/conversations?when=upcoming").json()
    assert [item["title"] for item in upcoming["items"]] == ["Soon", "Later"]

    past = client.get("/api/v1/conversations?when=past").json()
    assert [item["title"] for item in past["items"]] == ["Recent", "Older"]


def test_admin_get_returns_draft_detail(client, admin_token):
    created = create_conversation(client, admin_token)
    response = client.get(
        f"/api/v1/admin/conversations/{created['id']}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "draft"

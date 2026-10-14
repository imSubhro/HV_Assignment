from tests.conftest import auth_header


def request_payload(**overrides) -> dict:
    payload = {
        "full_name": "Asha Verma",
        "email": "asha@example.com",
        "phone": "+919876543210",
        "company_name": "GreenLoop Pvt Ltd",
        "funding_stage": "seed",
        "funding_amount": 5000000,
        "currency": "INR",
        "description": (
            "We are building a recycling marketplace and are raising seed "
            "funding to expand to five new cities over the next eighteen months."
        ),
    }
    payload.update(overrides)
    return payload


def submit_request(client, user_token, **overrides) -> dict:
    response = client.post(
        "/api/v1/investor-requests",
        json=request_payload(**overrides),
        headers=auth_header(user_token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_submit_without_token_returns_401(client):
    response = client.post("/api/v1/investor-requests", json=request_payload())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_new_request_is_pending_with_single_history_row(client, user_token, db):
    from app.models.investor_request import InvestorRequestStatusHistory

    created = submit_request(client, user_token)
    assert created["status"] == "pending"
    assert created["company_name"] == "GreenLoop Pvt Ltd"
    assert set(created) == {
        "id",
        "status",
        "full_name",
        "company_name",
        "funding_stage",
        "funding_amount",
        "currency",
        "created_at",
    }

    rows = db.query(InvestorRequestStatusHistory).all()
    assert len(rows) == 1
    assert rows[0].from_status is None
    assert rows[0].to_status.value == "pending"


def test_request_validation_rules(client, user_token):
    headers = auth_header(user_token)

    bad_phone = client.post(
        "/api/v1/investor-requests",
        json=request_payload(phone="12ab"),
        headers=headers,
    )
    assert bad_phone.status_code == 422

    short_description = client.post(
        "/api/v1/investor-requests",
        json=request_payload(description="too short"),
        headers=headers,
    )
    assert short_description.status_code == 422

    bad_amount = client.post(
        "/api/v1/investor-requests",
        json=request_payload(funding_amount=-5),
        headers=headers,
    )
    assert bad_amount.status_code == 422

    bad_stage = client.post(
        "/api/v1/investor-requests",
        json=request_payload(funding_stage="unknown"),
        headers=headers,
    )
    assert bad_stage.status_code == 422


def test_user_cannot_read_another_users_request(client, db, user_token):
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    other = User(
        full_name="Other Person",
        email="other-owner@example.com",
        password_hash=hash_password("StrongPass@123"),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(other)
    db.commit()

    other_token = client.post(
        "/api/v1/auth/login",
        json={"email": "other-owner@example.com", "password": "StrongPass@123"},
    ).json()["access_token"]

    mine = submit_request(client, user_token)
    theirs = submit_request(client, other_token, email="other-owner@example.com")

    assert (
        client.get(
            f"/api/v1/investor-requests/{theirs['id']}", headers=auth_header(user_token)
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/investor-requests/{mine['id']}", headers=auth_header(user_token)
        ).status_code
        == 200
    )


def test_me_lists_only_own_requests(client, db, user_token):
    from app.core.security import hash_password
    from app.models.user import User, UserRole

    other = User(
        full_name="Second Owner",
        email="second-owner@example.com",
        password_hash=hash_password("StrongPass@123"),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(other)
    db.commit()
    other_token = client.post(
        "/api/v1/auth/login",
        json={"email": "second-owner@example.com", "password": "StrongPass@123"},
    ).json()["access_token"]

    submit_request(client, user_token)
    submit_request(client, user_token, email="asha@example.com", company_name="Second Co")
    submit_request(client, other_token, email="second-owner@example.com")

    listing = client.get(
        "/api/v1/investor-requests/me", headers=auth_header(user_token)
    ).json()
    assert listing["total_items"] == 2
    assert {item["company_name"] for item in listing["items"]} == {
        "GreenLoop Pvt Ltd",
        "Second Co",
    }


def test_owner_detail_includes_history_but_not_admin_notes(
    client, user_token, admin_token
):
    created = submit_request(client, user_token)
    client.patch(
        f"/api/v1/admin/investor-requests/{created['id']}/status",
        json={"status": "under_review", "admin_notes": "Checking financials."},
        headers=auth_header(admin_token),
    )

    owner_view = client.get(
        f"/api/v1/investor-requests/{created['id']}", headers=auth_header(user_token)
    ).json()
    assert owner_view["status"] == "under_review"
    assert "admin_notes" not in owner_view
    assert len(owner_view["status_history"]) == 2
    assert owner_view["status_history"][0]["to_status"] == "pending"
    assert owner_view["status_history"][1]["to_status"] == "under_review"
    assert owner_view["status_history"][1]["note"] == "Checking financials."


def test_admin_list_filters_combine(client, admin_token, user_token):
    first = submit_request(
        client, user_token, company_name="Alpha Recycling", funding_stage="seed"
    )
    second = submit_request(
        client,
        user_token,
        email="asha@example.com",
        company_name="Beta Energy",
        funding_stage="series_a",
        funding_amount=25000000,
    )
    client.patch(
        f"/api/v1/admin/investor-requests/{first['id']}/status",
        json={"status": "under_review"},
        headers=auth_header(admin_token),
    )

    headers = auth_header(admin_token)
    everything = client.get("/api/v1/admin/investor-requests", headers=headers).json()
    assert everything["total_items"] == 2

    by_status = client.get(
        "/api/v1/admin/investor-requests?status=under_review", headers=headers
    ).json()
    assert by_status["total_items"] == 1
    assert by_status["items"][0]["id"] == first["id"]

    by_stage = client.get(
        "/api/v1/admin/investor-requests?funding_stage=series_a", headers=headers
    ).json()
    assert by_stage["total_items"] == 1
    assert by_stage["items"][0]["id"] == second["id"]

    by_search = client.get(
        "/api/v1/admin/investor-requests?search=beta", headers=headers
    ).json()
    assert by_search["total_items"] == 1

    today = client.get(
        "/api/v1/admin/investor-requests?from_date=2000-01-01&to_date=2100-01-01",
        headers=headers,
    ).json()
    assert today["total_items"] == 2

    no_results = client.get(
        "/api/v1/admin/investor-requests?from_date=1999-01-01&to_date=1999-01-02",
        headers=headers,
    ).json()
    assert no_results["total_items"] == 0

    combined = client.get(
        "/api/v1/admin/investor-requests?status=under_review&search=alpha",
        headers=headers,
    ).json()
    assert combined["total_items"] == 1


def test_invalid_status_transitions_return_400(client, admin_token, user_token):
    created = submit_request(client, user_token)
    headers = auth_header(admin_token)
    request_id = created["id"]

    assert client.patch(
        f"/api/v1/admin/investor-requests/{request_id}/status",
        json={"status": "approved"},
        headers=headers,
    ).status_code == 200

    back_to_pending = client.patch(
        f"/api/v1/admin/investor-requests/{request_id}/status",
        json={"status": "pending"},
        headers=headers,
    )
    assert back_to_pending.status_code == 400
    assert back_to_pending.json()["error"]["code"] == "BAD_REQUEST"

    again_approved = client.patch(
        f"/api/v1/admin/investor-requests/{request_id}/status",
        json={"status": "approved"},
        headers=headers,
    )
    assert again_approved.status_code == 400


def test_under_review_can_move_to_approved_or_rejected(client, admin_token, user_token):
    created = submit_request(client, user_token)
    headers = auth_header(admin_token)
    request_id = created["id"]

    under_review = client.patch(
        f"/api/v1/admin/investor-requests/{request_id}/status",
        json={"status": "under_review"},
        headers=headers,
    )
    assert under_review.status_code == 200

    rejected = client.patch(
        f"/api/v1/admin/investor-requests/{request_id}/status",
        json={"status": "rejected", "admin_notes": "Market size too small."},
        headers=headers,
    )
    assert rejected.status_code == 200
    body = rejected.json()
    assert body["status"] == "rejected"
    assert body["admin_notes"] == "Market size too small."
    assert body["reviewed_by"] is not None
    assert body["reviewed_at"] is not None
    assert len(body["status_history"]) == 3


def test_reject_without_notes_returns_422(client, admin_token, user_token):
    created = submit_request(client, user_token)
    response = client.patch(
        f"/api/v1/admin/investor-requests/{created['id']}/status",
        json={"status": "rejected"},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 422
    assert any(
        detail["field"] == "admin_notes"
        for detail in response.json()["error"]["details"]
    )

    stored = client.get(
        f"/api/v1/admin/investor-requests/{created['id']}",
        headers=auth_header(admin_token),
    ).json()
    assert stored["status"] == "pending"
    assert len(stored["status_history"]) == 1


def test_status_change_history_records_admin(client, admin_token, user_token, admin):
    created = submit_request(client, user_token)
    response = client.patch(
        f"/api/v1/admin/investor-requests/{created['id']}/status",
        json={"status": "under_review", "admin_notes": "Looking into it."},
        headers=auth_header(admin_token),
    )
    body = response.json()
    assert body["reviewed_by"] == admin["id"]
    assert body["status_history"][-1]["changed_by"] == admin["id"]
    assert body["status_history"][-1]["from_status"] == "pending"
    assert body["status_history"][-1]["to_status"] == "under_review"


def test_user_token_on_admin_investor_routes_returns_403(client, admin_token, user_token):
    created = submit_request(client, user_token)
    headers = auth_header(user_token)

    assert (
        client.get("/api/v1/admin/investor-requests", headers=headers).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/admin/investor-requests/{created['id']}", headers=headers
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/v1/admin/investor-requests/{created['id']}/status",
            json={"status": "approved"},
            headers=headers,
        ).status_code
        == 403
    )


def test_admin_detail_includes_review_metadata(client, admin_token, user_token):
    created = submit_request(client, user_token)
    client.patch(
        f"/api/v1/admin/investor-requests/{created['id']}/status",
        json={"status": "approved", "admin_notes": "Approved after diligence."},
        headers=auth_header(admin_token),
    )

    detail = client.get(
        f"/api/v1/admin/investor-requests/{created['id']}",
        headers=auth_header(admin_token),
    ).json()
    assert detail["admin_notes"] == "Approved after diligence."
    assert detail["reviewed_by"] is not None
    assert detail["reviewed_at"] is not None
    assert len(detail["status_history"]) == 2


def test_my_list_supports_status_filter_and_pagination(client, admin_token, user_token):
    first = submit_request(client, user_token)
    submit_request(client, user_token, email="asha@example.com", company_name="Second Co")
    client.patch(
        f"/api/v1/admin/investor-requests/{first['id']}/status",
        json={"status": "under_review"},
        headers=auth_header(admin_token),
    )

    headers = auth_header(user_token)
    pending = client.get(
        "/api/v1/investor-requests/me?status=pending", headers=headers
    ).json()
    assert pending["total_items"] == 1

    page = client.get("/api/v1/investor-requests/me?page=1&page_size=1", headers=headers)
    body = page.json()
    assert body["total_items"] == 2
    assert body["total_pages"] == 2
    assert len(body["items"]) == 1

from tests.conftest import register_and_login

NOW = "2026-03-10T10:00:00+00:00"
LATER = "2026-03-10T15:00:00+00:00"


def post_item(client, headers, **over):
    data = {"kind": "lost", "title": "Black Dell laptop", "description": "Black Dell laptop with stickers on lid",
            "category": "electronics", "location": "Central Library", "event_time": NOW}
    data.update(over)
    return client.post("/api/v1/items", data=data, headers=headers)


def test_auth_required(client):
    assert client.get("/api/v1/items").status_code == 401


def test_register_duplicate_and_refresh(client):
    register_and_login(client, "a@x.com")
    r = client.post("/api/v1/auth/register", json={"email": "a@x.com", "name": "Aa", "password": "password123"})
    assert r.status_code == 409
    tok = client.post("/api/v1/auth/login", data={"username": "a@x.com", "password": "password123"}).json()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r.status_code == 200
    # an access token must not work as a refresh token
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tok["access_token"]}).status_code == 401


def test_found_item_requires_secret_detail(client):
    h = register_and_login(client, "f@x.com")
    r = post_item(client, h, kind="found")
    assert r.status_code == 422


def test_full_lost_found_claim_return_flow(client):
    owner = register_and_login(client, "owner@x.com", "Owner")
    finder = register_and_login(client, "finder@x.com", "Finder")

    lost = post_item(client, owner).json()
    found = post_item(client, finder, kind="found", event_time=LATER, title="Dell laptop black",
                      description="Found black Dell laptop with stickers", secret_detail="Cracked bottom-left corner, sticker of a cat").json()

    # secret is hidden from the owner of the lost report, visible to the finder
    assert client.get(f"/api/v1/items/{found['id']}", headers=owner).json()["secret_detail"] is None
    assert client.get(f"/api/v1/items/{found['id']}", headers=finder).json()["secret_detail"]

    # the matcher paired them and notified both sides
    matches = client.get("/api/v1/items/matches/mine", headers=owner).json()
    assert len(matches) == 1 and matches[0]["score"] > 0.6
    assert client.get("/api/v1/notifications/unread-count", headers=owner).json()["count"] == 1

    # cannot claim own item, wrong kind
    assert client.post(f"/api/v1/items/{found['id']}/claims", json={"answer": "whatever it is"}, headers=finder).status_code == 400
    assert client.post(f"/api/v1/items/{lost['id']}/claims", json={"answer": "whatever it is"}, headers=owner).status_code == 400

    # good claim scores higher than a bad one
    good = client.post(f"/api/v1/items/{found['id']}/claims", headers=owner,
                       json={"answer": "bottom left corner is cracked and a cat sticker"}).json()
    other = register_and_login(client, "chancer@x.com", "Chancer")
    bad = client.post(f"/api/v1/items/{found['id']}/claims", headers=other, json={"answer": "it has a blue case"}).json()
    assert good["verification_score"] > bad["verification_score"]

    # only the finder can decide
    assert client.post(f"/api/v1/claims/{good['id']}/decision", json={"approve": True}, headers=owner).status_code == 403
    r = client.post(f"/api/v1/claims/{good['id']}/decision", json={"approve": True, "note": "ok"}, headers=finder)
    assert r.status_code == 200 and r.json()["status"] == "approved"

    # competing claim auto-rejected; item no longer claimable
    claims = client.get("/api/v1/claims/mine", headers=other).json()
    assert claims[0]["status"] == "rejected"
    assert client.get(f"/api/v1/items/{found['id']}", headers=finder).json()["status"] == "claimed"

    # handoff confirmation awards karma
    assert client.post(f"/api/v1/claims/{good['id']}/returned", headers=finder).status_code == 200
    assert client.get("/api/v1/auth/me", headers=finder).json()["karma"] == 10
    assert client.get("/api/v1/leaderboard", headers=owner).json()[0]["name"] == "Finder"


def test_filters_and_pagination(client):
    h = register_and_login(client, "p@x.com")
    for i in range(5):
        post_item(client, h, title=f"Keys {i}", category="keys", description="bunch of keys", location="Hostel")
    post_item(client, h, title="Phone", category="electronics")
    page = client.get("/api/v1/items?category=keys&size=2&page=3", headers=h).json()
    assert page["total"] == 5 and len(page["items"]) == 1
    assert client.get("/api/v1/items?q=phone", headers=h).json()["total"] == 1


def test_admin_endpoints_forbidden_for_students(client):
    h = register_and_login(client, "s@x.com")
    assert client.get("/api/v1/admin/users", headers=h).status_code == 403
    assert client.get("/api/v1/stats", headers=h).status_code == 200


def test_rejects_non_image_upload(client):
    h = register_and_login(client, "u@x.com")
    data = {"kind": "lost", "title": "Thing", "category": "other", "location": "Gate", "event_time": NOW}
    r = client.post("/api/v1/items", data=data, headers=h, files={"image": ("x.png", b"not an image", "image/png")})
    assert r.status_code == 400

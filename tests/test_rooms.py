def test_create_room_requires_auth(client):
    response = client.post("/rooms", json={"number": "101", "room_type": "single", "price_per_night": 89.0})
    assert response.status_code == 401


def test_create_room_authenticated(client, auth_headers):
    response = client.post(
        "/rooms",
        json={"number": "101", "room_type": "single", "price_per_night": 89.0},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["number"] == "101"
    assert data["is_active"] is True


def test_create_duplicate_room_number_fails(client, auth_headers):
    payload = {"number": "202", "room_type": "double", "price_per_night": 129.0}
    client.post("/rooms", json=payload, headers=auth_headers)
    response = client.post("/rooms", json=payload, headers=auth_headers)
    assert response.status_code == 400


def test_list_rooms_only_active_by_default(client, auth_headers):
    client.post("/rooms", json={"number": "301", "room_type": "suite", "price_per_night": 249.0}, headers=auth_headers)
    room2 = client.post(
        "/rooms", json={"number": "302", "room_type": "suite", "price_per_night": 249.0}, headers=auth_headers
    ).json()

    client.delete(f"/rooms/{room2['id']}", headers=auth_headers)

    response = client.get("/rooms")
    numbers = [r["number"] for r in response.json()]
    assert "301" in numbers
    assert "302" not in numbers


def test_get_room_not_found(client):
    response = client.get("/rooms/9999")
    assert response.status_code == 404


def test_invalid_price_rejected(client, auth_headers):
    response = client.post(
        "/rooms",
        json={"number": "401", "room_type": "single", "price_per_night": -10},
        headers=auth_headers,
    )
    assert response.status_code == 422

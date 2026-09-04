def _create_room(client, auth_headers, number="501"):
    response = client.post(
        "/rooms",
        json={"number": number, "room_type": "double", "price_per_night": 150.0},
        headers=auth_headers,
    )
    return response.json()["id"]


def test_create_reservation_success(client, auth_headers):
    room_id = _create_room(client, auth_headers)
    response = client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-10-01", "check_out": "2026-10-05"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "confirmed"


def test_reservation_check_out_before_check_in_rejected(client, auth_headers):
    room_id = _create_room(client, auth_headers)
    response = client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-10-05", "check_out": "2026-10-01"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_overlapping_reservation_rejected(client, auth_headers):
    room_id = _create_room(client, auth_headers)
    client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-11-01", "check_out": "2026-11-10"},
        headers=auth_headers,
    )
    response = client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-11-05", "check_out": "2026-11-07"},
        headers=auth_headers,
    )
    assert response.status_code == 409


def test_non_overlapping_reservation_succeeds(client, auth_headers):
    room_id = _create_room(client, auth_headers)
    client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-12-01", "check_out": "2026-12-05"},
        headers=auth_headers,
    )
    response = client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-12-05", "check_out": "2026-12-10"},
        headers=auth_headers,
    )
    assert response.status_code == 201


def test_reservation_on_inactive_room_fails(client, auth_headers):
    room_id = _create_room(client, auth_headers, number="601")
    client.delete(f"/rooms/{room_id}", headers=auth_headers)
    response = client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-10-01", "check_out": "2026-10-05"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_cancel_reservation(client, auth_headers):
    room_id = _create_room(client, auth_headers, number="701")
    res = client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-10-01", "check_out": "2026-10-05"},
        headers=auth_headers,
    ).json()

    response = client.post(f"/reservations/{res['id']}/cancel", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancelling_frees_up_dates(client, auth_headers):
    room_id = _create_room(client, auth_headers, number="801")
    res = client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-10-01", "check_out": "2026-10-05"},
        headers=auth_headers,
    ).json()
    client.post(f"/reservations/{res['id']}/cancel", headers=auth_headers)

    response = client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-10-02", "check_out": "2026-10-04"},
        headers=auth_headers,
    )
    assert response.status_code == 201


def test_list_my_reservations(client, auth_headers):
    room_id = _create_room(client, auth_headers, number="901")
    client.post(
        "/reservations",
        json={"room_id": room_id, "check_in": "2026-10-01", "check_out": "2026-10-05"},
        headers=auth_headers,
    )
    response = client.get("/reservations/me", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

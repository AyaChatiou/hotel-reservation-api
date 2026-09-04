def test_register_new_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123", "full_name": "Alice"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert "hashed_password" not in data


def test_register_duplicate_email_fails(client):
    payload = {"email": "bob@example.com", "password": "password123", "full_name": "Bob"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400


def test_login_success(client):
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "password123", "full_name": "Carol"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "carol@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_fails(client):
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "password123", "full_name": "Dave"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "dave@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_read_current_user_requires_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_read_current_user_with_token(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

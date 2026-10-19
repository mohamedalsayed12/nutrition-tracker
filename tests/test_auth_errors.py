from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token


ME = "/api/v1/users/me"


def test_missing_token_returns_401(client):
    response = client.get(ME)
    assert response.status_code == 401
    assert response.json == {"error": "Missing access token."}


@pytest.mark.parametrize("token", ["nope", "a.b.c", "eyJhbGciOiJIUzI1NiJ9.e30.bad-signature"])
def test_malformed_or_tampered_token_returns_401(client, token):
    response = client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json == {"error": "Invalid access token."}


def test_token_signed_with_another_key_returns_401(app, client, authorized_headers):
    good_token = authorized_headers["Authorization"].removeprefix("Bearer ")
    header, payload, signature = good_token.split(".")
    forged = f"{header}.{payload}.{signature[::-1]}"
    response = client.get(ME, headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_expired_token_returns_401(app, client, authorized_headers):
    with app.app_context():
        expired = create_access_token(identity="1", expires_delta=timedelta(seconds=-1))
    response = client.get(ME, headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json == {"error": "Access token has expired."}


def test_valid_token_still_works(client, authorized_headers):
    assert client.get(ME, headers=authorized_headers).status_code == 200

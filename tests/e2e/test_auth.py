from asyncio import sleep
from datetime import datetime
from urllib.parse import urlsplit

from httpx import AsyncClient
import pyotp
from tests.e2e.conftest import TEST_USER_PASSWORD, TEST_USER_USERNAME, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD

TEST_USER_EMAIL = f"{-int(datetime.now().timestamp())}@gmail.com"

TEST_PASSWORD = "password"


async def test_auth_flow(client: AsyncClient, email_client: AsyncClient):
    """
    POST    "/api/v1/auth/register"
    POST    "/api/v1/auth/login"
    GET     "/api/v1/users/me"
    POST    "/api/v1/auth/refresh"
    """

    # 1. Test register
    init_user_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_PASSWORD,
        "username": TEST_USER_EMAIL,
        "role_name": "user",
    }

    response = await client.post(
        "/api/v1/auth/register",
        json=init_user_data,
    )
    assert response.status_code == 202

    created_user = response.json()
    assert created_user["email"] == init_user_data["email"]

    # 1.1. Confirming email
    response = await email_client.get("/api/v1/messages")

    for message in response.json()["messages"]:
        if any([receiver["Address"] == created_user["email"] for receiver in message["To"]]):
            snippet = message["Snippet"]
            confirm_email_link = snippet.split("Click the link to verify your email: ")[1]
            break

    assert confirm_email_link, confirm_email_link

    response = await client.get(confirm_email_link)

    # 2. Test login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_USER_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["token_type"] == "Bearer"
    assert data["access_token"]
    assert data["refresh_token"]

    # 3. Test access_token
    access_token = f"{data['token_type']} {data['access_token']}"
    refresh_token = data["refresh_token"]

    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": access_token,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert init_user_data["email"] == data["email"]
    assert init_user_data["username"] == data["username"]
    assert "password" not in data

    # 4. Test refresh tokens
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200


async def test_expired_access_token_denied(client: AsyncClient):
    """
    POST    "/api/v1/auth/login"
    sleep   4 seconds
    GET     "/api/v1/users/me"      - after access token expiry
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_ADMIN_USERNAME,
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]

    await sleep(4)
    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": access_token,
        },
    )

    assert response.status_code == 401


async def test_logout(client: AsyncClient):
    """
    POST    "/api/v1/auth/login"
    POST    "/api/v1/auth/logout"
    GET     "/api/v1/users/me"      - after access token expiry
    """

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_USER_USERNAME,
            "password": TEST_USER_PASSWORD,
        },
    )

    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 204

    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": access_token,
        },
    )

    assert response.status_code == 401


async def test_enable_mfa(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_USER_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["token_type"] == "Bearer"
    assert data["access_token"]

    access_token = f"{data['token_type']} {data['access_token']}"

    ### enable mfa
    response = await client.post(
        "/api/v1/auth/mfa/enable",
        headers={
            "Authorization": access_token,
        },
    )

    assert response.status_code == 200
    response_data = response.json()

    assert "uri" in response_data
    assert "challenge_token" in response_data

    uri = response_data["uri"]
    secret_part = uri.split("secret=")[1].split("&")[0]
    secret = secret_part.strip()

    assert len(secret) >= 16, "Secret to short"

    totp = pyotp.TOTP(secret)
    code = totp.now()

    ### confirm enable mfa
    response = await client.post(
        "/api/v1/auth/mfa/verify",
        json={
            "code": code,
            "challenge_token": response_data["challenge_token"],
        },
    )
    if response.status_code == 400:
        totp = pyotp.TOTP(secret)
        code = totp.now()

        response = await client.post(
            "/api/v1/auth/mfa/verify",
            json={
                "code": code,
                "challenge_token": response_data["challenge_token"],
            },
        )

    assert response.status_code == 200, response.json()

    response = await client.post(
        "/api/v1/auth/mfa/disable",
        headers={
            "Authorization": access_token,
        },
    )
    assert response.status_code == 200
    response_data = response.json()

    assert "uri" in response_data
    assert "challenge_token" in response_data

    uri = response_data["uri"]
    secret_part = uri.split("secret=")[1].split("&")[0]
    secret = secret_part.strip()

    assert len(secret) >= 16, "Secret to short"

    totp = pyotp.TOTP(secret)
    code = totp.now()

    ### confirm disable mfa
    response = await client.post(
        "/api/v1/auth/mfa/verify",
        json={
            "code": code,
            "challenge_token": response_data["challenge_token"],
        },
    )
    if response.status_code == 400:
        totp = pyotp.TOTP(secret)
        code = totp.now()

        response = await client.post(
            "/api/v1/auth/mfa/verify",
            json={
                "code": code,
                "challenge_token": response_data["challenge_token"],
            },
        )

    assert response.status_code == 200, response.json()


async def test_reset_password_via_email(client, email_client):
    # 1. Start reset password
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"email": TEST_USER_EMAIL},
    )
    assert response.status_code == 200

    # 2. Confirm reset password via email
    response = await email_client.get("/api/v1/messages")

    for message in response.json()["messages"]:
        if any([receiver["Address"] == TEST_USER_EMAIL for receiver in message["To"]]):
            snippet = message["Snippet"]
            confirm_email_link = snippet.split("Click the link to reset your password: ")[1]
            break

    assert confirm_email_link, confirm_email_link
    parsed_url = urlsplit(confirm_email_link)
    url = parsed_url.path
    token = parsed_url.query.split("=")[1]

    response = await client.get(url)

    NEW_TEST_PASSWORD = "new_password"

    response = await client.post(
        url, data={"token": token, "new_password": NEW_TEST_PASSWORD, "confirm_password": NEW_TEST_PASSWORD}
    )
    assert response.status_code == 200, response.json()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_USER_EMAIL,
            "password": NEW_TEST_PASSWORD,
        },
    )

    assert response.status_code == 200, response.json()

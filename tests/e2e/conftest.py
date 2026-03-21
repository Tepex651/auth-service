import asyncio
from datetime import datetime
import os

import pytest
from httpx import AsyncClient


TEST_ADMIN_USERNAME = "admin"
TEST_ADMIN_PASSWORD = "password"
TEST_USER_USERNAME = "user"
TEST_USER_PASSWORD = "password"
base_url = os.getenv("BASE_URL", "http://localhost:8000")
base_mail_url = os.getenv("BASE_MAIL_URL", "http://localhost:8025")


@pytest.fixture
async def client():
    async with AsyncClient(base_url=base_url, timeout=15.0) as client:
        yield client


@pytest.fixture
async def email_client():
    async with AsyncClient(base_url=base_mail_url, timeout=15.0) as client:
        yield client

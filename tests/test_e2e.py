from fastapi import FastAPI
import httpx
import pytest
import pytest_asyncio
from starlette.testclient import TestClient

from conftest import User, UserNotFoundError
from fastclient import FastClient


@pytest.fixture
def sync_client(app: FastAPI):
    with FastClient(base_url="http://testserver", app=app) as client:
        client._http = TestClient(app)
        yield client

@pytest_asyncio.fixture
async def async_client(app: FastAPI):
    async with FastClient(base_url="http://testserver", app=app) as client:
        client._http = httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url=client.base_url,
        )
        yield client


def test_e2e_get_users_list(sync_client):
    """Test end-to-end fetching a list of users and verifying Pydantic deserialization."""
    users = sync_client.get_users()
    assert len(users) == 1
    assert isinstance(users[0], User)
    assert users[0].id == "1"
    assert users[0].name == "Alice"


def test_e2e_get_single_user_success(sync_client):
    """Test end-to-end path parameter formatting and single model return."""
    user = sync_client.get_user(user_id="1")
    assert isinstance(user, User)
    assert user.id == "1"
    assert user.name == "Alice"


def test_e2e_create_user_success(sync_client):
    """Test end-to-end POST request sending a Pydantic body parameter."""
    new_user = User(id="2", name="Bob")
    created = sync_client.create_user(user=new_user)
    assert isinstance(created, User)
    assert created.id == "2"
    assert created.name == "Bob"


def test_e2e_custom_exception_auto_raised(sync_client):
    """Test end-to-end raising and catching custom BaseAPIException subclass (404)."""
    with pytest.raises(UserNotFoundError) as exc_info:
        sync_client.get_user(user_id="999")

    err = exc_info.value
    assert err.status_code == 404
    assert err.message == "User not found"
    assert err.details == {"user_id": "999"}


@pytest.mark.asyncio
async def test_async_e2e_get_users_list(async_client):
    """Test end-to-end fetching a list of users and verifying Pydantic deserialization."""
    users = await async_client.get_users()
    assert len(users) == 1
    assert isinstance(users[0], User)
    assert users[0].id == "1"
    assert users[0].name == "Alice"


@pytest.mark.asyncio
async def test_async_e2e_get_single_user_success(async_client):
    """Test end-to-end path parameter formatting and single model return."""
    user = await async_client.get_user(user_id="1")
    assert isinstance(user, User)
    assert user.id == "1"
    assert user.name == "Alice"


@pytest.mark.asyncio
async def test_async_e2e_create_user_success(async_client):
    """Test end-to-end POST request sending a Pydantic body parameter."""
    new_user = User(id="2", name="Bob")
    created = await async_client.create_user(user=new_user)
    assert isinstance(created, User)
    assert created.id == "2"
    assert created.name == "Bob"


@pytest.mark.asyncio
async def test_async_e2e_custom_exception_auto_raised(async_client):
    """Test end-to-end raising and catching custom BaseAPIException subclass (404)."""
    with pytest.raises(UserNotFoundError) as exc_info:
        await async_client.get_user(user_id="999")

    err = exc_info.value
    assert err.status_code == 404
    assert err.message == "User not found"
    assert err.details == {"user_id": "999"}

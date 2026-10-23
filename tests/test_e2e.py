from fastapi import FastAPI
import pytest
from starlette.testclient import TestClient as StarletteTestClient

from conftest import User, UserNotFoundError
from fast_client import FastClient


@pytest.fixture
def client(app: FastAPI):
    fast_client = FastClient(base_url="http://testserver", app=app)
    fast_client._http = StarletteTestClient(app, base_url="http://testserver")
    return fast_client


def test_e2e_get_users_list(client):
    """Test end-to-end fetching a list of users and verifying Pydantic deserialization."""
    users = client.get_users()
    assert len(users) == 1
    assert isinstance(users[0], User)
    assert users[0].id == "1"
    assert users[0].name == "Alice"


def test_e2e_get_single_user_success(client):
    """Test end-to-end path parameter formatting and single model return."""
    user = client.get_user(user_id="1")
    assert isinstance(user, User)
    assert user.id == "1"
    assert user.name == "Alice"


def test_e2e_create_user_success(client):
    """Test end-to-end POST request sending a Pydantic body parameter."""
    new_user = User(id="2", name="Bob")
    created = client.create_user(user=new_user)
    assert isinstance(created, User)
    assert created.id == "2"
    assert created.name == "Bob"


def test_e2e_custom_exception_auto_raised(client):
    """Test end-to-end raising and catching custom BaseAPIException subclass (404)."""
    with pytest.raises(UserNotFoundError) as exc_info:
        client.get_user(user_id="999")

    err = exc_info.value
    assert err.status_code == 404
    assert err.message == "User not found"
    assert err.details == {"user_id": "999"}

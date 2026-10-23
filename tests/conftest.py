from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import pytest

from fastclient import BaseAPIException, register_exceptions


class User(BaseModel):
    id: str
    name: str


class UserNotFoundError(BaseAPIException):
    status_code = 404
    message = "User not found"

class UserAlreadyExistsError(BaseAPIException):
    status_code = 409
    message = "User already exists"


@pytest.fixture
def app() -> FastAPI:
    fastapi_app = FastAPI()
    register_exceptions(fastapi_app)

    db: dict[str, User] = {
        "1": User(id="1", name="Alice"),
    }

    @fastapi_app.get("/users", response_model=List[User])
    def get_users():
        return list(db.values())

    @fastapi_app.get("/users/{user_id}", response_model=User)
    def get_user(user_id: str):
        if user_id not in db:
            raise UserNotFoundError(details={"user_id": user_id})
        return db[user_id]

    @fastapi_app.post("/users", response_model=User)
    def create_user(user: User):
        if user.id in db:
            raise UserAlreadyExistsError()
        db[user.id] = user
        return user

    return fastapi_app

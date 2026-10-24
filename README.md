# FastClient

A lightweight, dynamic Python client for FastAPI applications that automatically maps API routes into native pythonic methods with seamless Pydantic model deserialization and custom exception propagation.

---

## Features

- **Dynamic Route Binding**: Converts FastAPI `APIRoute` metadata directly into native client instance methods.
- **Pydantic Model Deserialization**: Parses input request payloads and automatically validates response models.
- **Custom Exception Auto-Raising**: Captures structured server error payloads (`ErrorDetail`) and raises matching custom Python exception classes.

---

## Installation

Install `fastclient` alongside your FastAPI dependencies:

```bash
pip install fastclient
```

## Quickstart
Define Server Models & Custom Exceptions
```python
from fastapi import FastAPI
from pydantic import BaseModel
from fastclient import BaseAPIException, register_exceptions

app = FastAPI()

# Register exception handlers on your FastAPI app
register_exceptions(app)


class User(BaseModel):
    id: str
    name: str


class UserNotFoundError(BaseAPIException):
    status_code = 404
    message = "User not found"


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    if user_id != "1":
        raise UserNotFoundError(details={"user_id": user_id})
    return User(id="1", name="Alice")
```

### 2. Instantiate and Call `FastClient`

`FastClient` requires a context manager session to manage network resources and connections. Use standard `with` for synchronous execution or `async with` for asynchronous calls.

#### Synchronous Usage (`with`)

```python
from fastclient import FastClient

# 1. Successful request returning Pydantic User instance
with FastClient(base_url="http://localhost:8000", app=app) as client:
    user = client.get_user(user_id="1")
    print(user.name)  # Output: "Alice"

    # 2. Failed request automatically raising your custom exception
    try:
        client.get_user(user_id="999")
    except UserNotFoundError as err:
        print(err.status_code)  # Output: 404
        print(err.message)      # Output: "User not found"
        print(err.details)      # Output: {'user_id': '999'}
```

#### Asynchronous Usage (`async with`)
```python
import asyncio
from fastclient import FastClient

async def main():
    async with FastClient(base_url="http://localhost:8000", app=app) as client:
        # 1. Async successful request
        user = await client.get_user(user_id="1")
        print(user.name)  # Output: "Alice"

        # 2. Async failed request
        try:
            await client.get_user(user_id="999")
        except UserNotFoundError as err:
            print(err.status_code)  # Output: 404
            print(err.message)      # Output: "User not found"

asyncio.run(main())
```

## Development & Testing
fastclient uses `uv` and standard `pytest` for development and testing.
### Install Development Dependencies
```bash
uv sync --dev
```
### Run Tests
Execute unit and end-to-end integration tests:
```bash
uv run pytest
```

## Author

- **Ron Weisenstern** - [@ronviz](https://github.com/ronviz)

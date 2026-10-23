import importlib
from typing import Union
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fast_client.asgi import resolve_app
from fast_client.base_exception import BaseAPIException


def register_exceptions(app: Union[FastAPI, str]) -> None:
    """Registers global exception handling for all BaseAPIException subclasses.

    Accepts either a FastAPI application instance or a string path (e.g., 'server.app:app').
    """
    resolved_app = resolve_app(app)

    @resolved_app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException):
        detail = exc.to_detail()
        return JSONResponse(
            status_code=detail.status_code,
            content=detail.model_dump(),
        )

from fastapi import FastAPI
import httpx
import pytest

from fast_client import BaseAPIException
from fast_client.asgi import resolve_app
from fast_client.client import FastClient


def test_resolve_app_instance(app: FastAPI):
    """Test resolve_app with a live FastAPI instance."""
    resolved = resolve_app(app)
    assert isinstance(resolved, FastAPI)


def test_resolve_app_invalid_type():
    """Test resolve_app raises TypeError when passed an unsupported type."""
    with pytest.raises(TypeError, match="Expected FastAPI instance or string"):
        resolve_app(123)  # type: ignore


def test_raise_for_api_error_ignores_success():
    """Test that _raise_for_api_error does nothing on 2xx responses."""
    response = httpx.Response(200, json={"message": "ok"})
    # Should complete without raising any exception
    FastClient._raise_for_api_error(response)


def test_raise_for_api_error_fallback_httpx_error():
    """Test fallback to standard HTTPStatusError when payload isn't ErrorDetail JSON."""
    request = httpx.Request("GET", "http://testserver/error")
    response = httpx.Response(
        500, json={"error": "Internal Server Error"}, request=request
    )

    with pytest.raises(httpx.HTTPStatusError):
        FastClient._raise_for_api_error(response)

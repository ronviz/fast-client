from typing import Any, Callable, Dict, Sequence, Tuple, Union, cast
from fastapi import FastAPI
from fastapi.routing import APIRoute
import httpx
from pydantic import BaseModel, ValidationError

from fast_client.asgi import resolve_app
from fast_client.base_exception import BaseAPIException, ErrorDetail


class FastClient:
    """Dynamically binds FastAPI routes as native client methods using APIRoute metadata."""

    def __init__(
        self,
        base_url: str,
        app: Union[FastAPI, str],
    ):
        self.base_url = base_url.rstrip("/")
        self._app = resolve_app(app)
        self._http = httpx.Client(base_url=self.base_url)

        self._bind_app_routes()

    @staticmethod
    def _raise_for_api_error(response: httpx.Response) -> None:
        """Parses non-2xx responses and raises the matching custom exception if registered."""
        if response.is_success:
            return

        try:
            data = response.json()
            detail = ErrorDetail(**data)

            exc_cls = BaseAPIException.get_registered_exception(detail.error_type)
            if exc_cls is None:
                exc_cls = BaseAPIException

            raise exc_cls(
                message=detail.message,
                status_code=detail.status_code,
                details=detail.details,
            )
        except (ValueError, ValidationError):
            response.raise_for_status()

    @staticmethod
    def _format_path_params(
        path_template: str, route: APIRoute, kwargs: Dict[str, Any]
    ) -> str:
        """Formats the URL path using APIRoute's recognized path_params metadata."""
        formatted_path = path_template
        path_param_names = {field.name for field in route.dependant.path_params}

        for param_name in path_param_names:
            if param_name in kwargs:
                val = kwargs.pop(param_name)
                formatted_path = formatted_path.replace(f"{{{param_name}}}", str(val))

        return formatted_path

    @staticmethod
    def _extract_body_param(route: APIRoute, kwargs: Dict[str, Any]) -> Any:
        """Extracts JSON body parameters using APIRoute's body_params metadata."""
        body_param_names = {field.name for field in route.dependant.body_params}
        if not body_param_names:
            return None

        # Single body parameter (e.g. `user: User`)
        if len(body_param_names) == 1:
            param_name = next(iter(body_param_names))
            if param_name in kwargs:
                val = kwargs.pop(param_name)
                return (
                    val.model_dump(mode="json") if hasattr(val, "model_dump") else val
                )

        # Multiple body parameters combined into a dictionary
        body_dict = {}
        for param_name in list(body_param_names):
            if param_name in kwargs:
                val = kwargs.pop(param_name)
                body_dict[param_name] = (
                    val.model_dump(mode="json") if hasattr(val, "model_dump") else val
                )
        return body_dict if body_dict else None

    @staticmethod
    def _extract_query_params(
        route: APIRoute, kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extracts remaining query parameters using APIRoute's query_params metadata."""
        query_param_names = {field.name for field in route.dependant.query_params}
        query_params = {}

        for param_name in query_param_names:
            if param_name in kwargs:
                query_params[param_name] = kwargs.pop(param_name)

        return query_params

    @staticmethod
    def _deserialize_response(route: APIRoute, response: httpx.Response) -> Any:
        """Parses response body into Pydantic models via response_model."""
        response_cls = route.response_model
        if not response_cls or not response.is_success:
            return response.json()

        raw_json = response.json()
        if hasattr(response_cls, "model_validate") and isinstance(raw_json, dict):
            return response_cls.model_validate(raw_json)

        if isinstance(raw_json, list) and hasattr(response_cls, "__args__"):
            item_cls = response_cls.__args__[0]
            if hasattr(item_cls, "model_validate"):
                return [item_cls.model_validate(i) for i in raw_json]

        return raw_json

    def _bind_app_routes(self) -> None:
        """Iterates over app.routes and dynamically attaches methods."""
        for route in self._app.routes:
            if not isinstance(route, APIRoute):
                continue

            method_name = route.endpoint.__name__
            bound_method = self._create_route_method(route)
            setattr(self, method_name, bound_method)

    def _create_route_method(self, route: APIRoute) -> Callable[..., Any]:
        """Generates a callable client method using APIRoute metadata."""
        http_method = next(iter(route.methods)).lower()

        def route_method(**kwargs) -> Any:
            # Copy kwargs so we can pop values as we categorize them
            input_kwargs = dict(kwargs)

            # 1. Map parameters using APIRoute metadata
            formatted_path = self._format_path_params(route.path, route, input_kwargs)
            json_body = self._extract_body_param(route, input_kwargs)
            query_params = self._extract_query_params(route, input_kwargs)

            # 2. Execute HTTP request
            response = self._http.request(
                method=http_method,
                url=formatted_path,
                params=query_params if query_params else None,
                json=json_body,
            )

            # 3. Handle errors & return deserialized body
            self._raise_for_api_error(response)
            return self._deserialize_response(route, response)

        # Preserve original docstring and endpoint name
        route_method.__name__ = route.endpoint.__name__
        route_method.__doc__ = route.endpoint.__doc__

        return route_method


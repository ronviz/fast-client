import importlib
from typing import Union
from fastapi import FastAPI


def resolve_app(app_input: Union[FastAPI, str]) -> FastAPI:
    """Resolves a FastAPI instance or a Uvicorn-style string import path ('module.submodule:app')."""
    if isinstance(app_input, FastAPI):
        return app_input

    if isinstance(app_input, str):
        if ":" not in app_input:
            raise ValueError(
                f"Invalid app string path '{app_input}'. Must be in 'module:attribute' format (e.g., 'server.app:app')."
            )

        module_path, app_name = app_input.split(":", 1)
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(
                f"Could not import module '{module_path}' from string path '{app_input}'."
            ) from e

        try:
            app_obj = getattr(module, app_name)
        except AttributeError as e:
            raise AttributeError(
                f"Module '{module_path}' has no attribute '{app_name}'."
            ) from e

        if not isinstance(app_obj, FastAPI):
            raise TypeError(
                f"Object '{app_name}' in module '{module_path}' is of type {type(app_obj)}, expected FastAPI."
            )

        return app_obj

    raise TypeError(
        f"Expected FastAPI instance or string import path ('module:app'), got {type(app_input)}"
    )

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Unified wire-format schema for API exception responses."""

    error_type: str
    message: str
    status_code: int = 500
    details: Optional[Dict[str, Any]] = None


class BaseAPIException(Exception):
    """Base exception for all service-specific custom exceptions.

    Subclasses automatically register themselves in the global registry
    via __init_subclass__ for client-side re-hydration.
    """

    status_code: int = 500
    _registry: Dict[str, Type["BaseAPIException"]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Register every concrete subclass by its class name
        cls._registry[cls.__name__] = cls

    def __init__(
        self,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}

    def to_detail(self) -> ErrorDetail:
        """Serializes the exception instance to an ErrorDetail model."""
        return ErrorDetail(
            error_type=self.__class__.__name__,
            message=self.message,
            status_code=self.status_code,
            details=self.details,
        )

    @classmethod
    def get_registered_exception(
        cls, error_type: str
    ) -> Optional[Type["BaseAPIException"]]:
        """Looks up a registered exception class by its name string."""
        return cls._registry.get(error_type)

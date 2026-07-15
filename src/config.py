from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import os
import secrets


class ConfigurationError(RuntimeError):
    """Raised when security-sensitive application configuration is invalid."""


_PLACEHOLDER_MARKERS = (
    "change-me",
    "changeme",
    "your-secret",
    "your_secret",
    "placeholder",
    "example-secret",
)


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def _parse_origins(raw: str) -> tuple[str, ...]:
    origins = tuple(dict.fromkeys(item.strip() for item in raw.split(",") if item.strip()))
    if not origins:
        raise ConfigurationError("CORS_ORIGINS must contain at least one origin.")
    return origins


def _parse_positive_int(raw: str, name: str, *, minimum: int, maximum: int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://") :]
    return value


@dataclass(frozen=True)
class Settings:
    environment: str
    secret_key: str
    database_url: str
    api_write_token: str
    cors_origins: tuple[str, ...]
    max_content_length: int

    @property
    def is_production(self) -> bool:
        return self.environment in {"production", "prod"}

    def to_flask_config(self) -> dict[str, object]:
        return {
            "APP_ENV": self.environment,
            "SECRET_KEY": self.secret_key,
            "SQLALCHEMY_DATABASE_URI": self.database_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "API_WRITE_TOKEN": self.api_write_token,
            "CORS_ORIGINS": self.cors_origins,
            "MAX_CONTENT_LENGTH": self.max_content_length,
            "AUTO_CREATE_DB": True,
        }


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if environ is None else environ
    environment = (source.get("APP_ENV") or source.get("FLASK_ENV") or "development").strip().lower()
    is_production = environment in {"production", "prod"}

    secret_key = (source.get("SECRET_KEY") or "").strip()
    if not secret_key:
        if is_production:
            raise ConfigurationError("SECRET_KEY is required in production.")
        secret_key = secrets.token_urlsafe(32)
    elif is_production and (len(secret_key) < 32 or _is_placeholder(secret_key)):
        raise ConfigurationError("SECRET_KEY must be a non-placeholder value of at least 32 characters.")

    api_write_token = (source.get("API_WRITE_TOKEN") or "").strip()
    if api_write_token and (len(api_write_token) < 24 or _is_placeholder(api_write_token)):
        raise ConfigurationError("API_WRITE_TOKEN must be a non-placeholder value of at least 24 characters.")

    cors_origins = _parse_origins(
        source.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )
    if is_production and "*" in cors_origins:
        raise ConfigurationError("Wildcard CORS origins are not allowed in production.")

    database_url = _normalize_database_url(
        (source.get("DATABASE_URL") or "sqlite:///users.db").strip()
    )
    max_content_length = _parse_positive_int(
        source.get("MAX_CONTENT_LENGTH", "65536"),
        "MAX_CONTENT_LENGTH",
        minimum=1024,
        maximum=1_048_576,
    )

    return Settings(
        environment=environment,
        secret_key=secret_key,
        database_url=database_url,
        api_write_token=api_write_token,
        cors_origins=cors_origins,
        max_content_length=max_content_length,
    )

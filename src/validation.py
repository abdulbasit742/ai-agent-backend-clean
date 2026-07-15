from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALLOWED_FIELDS = {"username", "email"}


def _clean_text(value: Any, field: str, *, minimum: int, maximum: int) -> tuple[str | None, str | None]:
    if not isinstance(value, str):
        return None, f"{field} must be a string."
    cleaned = value.strip()
    if not minimum <= len(cleaned) <= maximum:
        return None, f"{field} must be between {minimum} and {maximum} characters."
    if any(ord(character) < 32 for character in cleaned):
        return None, f"{field} contains unsupported control characters."
    return cleaned, None


def validate_user_payload(payload: Any, *, partial: bool = False) -> tuple[dict[str, str], dict[str, str]]:
    if not isinstance(payload, Mapping):
        return {}, {"body": "A JSON object is required."}

    unknown = sorted(set(payload) - _ALLOWED_FIELDS)
    if unknown:
        return {}, {"body": f"Unknown field(s): {', '.join(unknown)}."}

    required = set() if partial else _ALLOWED_FIELDS
    missing = sorted(field for field in required if field not in payload)
    if missing:
        return {}, {"body": f"Missing field(s): {', '.join(missing)}."}

    if partial and not any(field in payload for field in _ALLOWED_FIELDS):
        return {}, {"body": "At least one editable field is required."}

    cleaned: dict[str, str] = {}
    errors: dict[str, str] = {}

    if "username" in payload:
        username, error = _clean_text(payload["username"], "username", minimum=2, maximum=80)
        if error:
            errors["username"] = error
        elif username is not None:
            cleaned["username"] = username

    if "email" in payload:
        email, error = _clean_text(payload["email"], "email", minimum=5, maximum=254)
        if error:
            errors["email"] = error
        elif email is not None:
            normalized = email.lower()
            if not _EMAIL_RE.fullmatch(normalized):
                errors["email"] = "email must be a valid address."
            else:
                cleaned["email"] = normalized

    return cleaned, errors

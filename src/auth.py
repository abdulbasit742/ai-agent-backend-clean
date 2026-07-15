from __future__ import annotations

from functools import wraps
from hmac import compare_digest
from typing import Any, Callable, TypeVar, cast

from flask import current_app, jsonify, request

F = TypeVar("F", bound=Callable[..., Any])


def require_write_token(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        configured = str(current_app.config.get("API_WRITE_TOKEN") or "")
        if not configured:
            return jsonify({
                "status": "error",
                "message": "Write operations are disabled until API_WRITE_TOKEN is configured.",
            }), 503

        supplied = request.headers.get("X-API-Key", "")
        if not supplied or not compare_digest(supplied, configured):
            return jsonify({"status": "error", "message": "A valid X-API-Key is required."}), 401
        return view(*args, **kwargs)

    return cast(F, wrapped)

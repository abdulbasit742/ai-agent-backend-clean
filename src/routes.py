from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .auth import require_write_token
from .extensions import db
from .models import User
from .validation import validate_user_payload

api = Blueprint("api", __name__, url_prefix="/api")


def _get_user(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def _pagination_value(name: str, default: int, maximum: int) -> tuple[int | None, tuple[object, int] | None]:
    raw = request.args.get(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, (jsonify({"status": "error", "message": f"{name} must be an integer."}), 400)
    if value < 1 or value > maximum:
        return None, (
            jsonify({"status": "error", "message": f"{name} must be between 1 and {maximum}."}),
            400,
        )
    return value, None


def _duplicate_exists(username: str | None, email: str | None, *, exclude_id: int | None = None) -> bool:
    clauses = []
    if username is not None:
        clauses.append(User.username == username)
    if email is not None:
        clauses.append(User.email == email)
    if not clauses:
        return False
    statement = db.select(User.id).where(or_(*clauses))
    if exclude_id is not None:
        statement = statement.where(User.id != exclude_id)
    return db.session.scalar(statement.limit(1)) is not None


@api.get("")
def api_index():
    return jsonify({
        "service": "ai-agent-backend-clean",
        "version": "1.0.0",
        "endpoints": ["/api/health", "/api/users"],
    })


@api.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        current_app.logger.exception("Database health check failed")
        return jsonify({"status": "degraded", "database": "unavailable"}), 503
    return jsonify({
        "status": "healthy",
        "database": "available",
        "writes_enabled": bool(current_app.config.get("API_WRITE_TOKEN")),
    })


@api.get("/users")
def list_users():
    page, error = _pagination_value("page", 1, 100_000)
    if error:
        return error
    per_page, error = _pagination_value("per_page", 20, 100)
    if error:
        return error

    pagination = db.paginate(
        db.select(User).order_by(User.id.asc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )
    return jsonify({
        "items": [user.to_dict() for user in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
            "total": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    })


@api.post("/users")
@require_write_token
def create_user():
    cleaned, errors = validate_user_payload(request.get_json(silent=True))
    if errors:
        return jsonify({"status": "error", "errors": errors}), 400
    if _duplicate_exists(cleaned["username"], cleaned["email"]):
        return jsonify({"status": "error", "message": "Username or email already exists."}), 409

    user = User(**cleaned)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Username or email already exists."}), 409
    return jsonify(user.to_dict()), 201


@api.get("/users/<int:user_id>")
def get_user(user_id: int):
    user = _get_user(user_id)
    if user is None:
        return jsonify({"status": "error", "message": "User not found."}), 404
    return jsonify(user.to_dict())


@api.patch("/users/<int:user_id>")
@require_write_token
def update_user(user_id: int):
    user = _get_user(user_id)
    if user is None:
        return jsonify({"status": "error", "message": "User not found."}), 404

    cleaned, errors = validate_user_payload(request.get_json(silent=True), partial=True)
    if errors:
        return jsonify({"status": "error", "errors": errors}), 400
    if _duplicate_exists(cleaned.get("username"), cleaned.get("email"), exclude_id=user.id):
        return jsonify({"status": "error", "message": "Username or email already exists."}), 409

    for field, value in cleaned.items():
        setattr(user, field, value)
    user.touch()
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Username or email already exists."}), 409
    return jsonify(user.to_dict())


@api.delete("/users/<int:user_id>")
@require_write_token
def delete_user(user_id: int):
    user = _get_user(user_id)
    if user is None:
        return jsonify({"status": "error", "message": "User not found."}), 404
    db.session.delete(user)
    db.session.commit()
    return "", 204

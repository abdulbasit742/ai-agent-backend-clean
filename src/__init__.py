from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def create_app(
    test_config: Mapping[str, Any] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
):
    """Create and configure the Flask application."""

    import os

    from flask import Flask, jsonify
    from flask_cors import CORS

    from .config import load_settings
    from .extensions import db

    settings = load_settings(environ)
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(settings.to_flask_config())
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    CORS(
        app,
        resources={r"/api/*": {"origins": list(app.config["CORS_ORIGINS"])}},
        supports_credentials=False,
        methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    from .routes import api

    app.register_blueprint(api)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"status": "error", "message": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"status": "error", "message": "Method not allowed."}), 405

    @app.errorhandler(413)
    def payload_too_large(_error):
        return jsonify({"status": "error", "message": "Request body is too large."}), 413

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        app.logger.exception("Unhandled request error")
        return jsonify({"status": "error", "message": "Internal server error."}), 500

    if app.config.get("AUTO_CREATE_DB", True):
        with app.app_context():
            from . import models  # noqa: F401

            db.create_all()

    return app

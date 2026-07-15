from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from src import create_app
from src.extensions import db


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test.db"
        self.token = "test-write-token-with-enough-length"
        self.app = create_app(
            {"TESTING": True},
            environ={
                "APP_ENV": "test",
                "SECRET_KEY": "test-secret-key-with-enough-length-123",
                "API_WRITE_TOKEN": self.token,
                "DATABASE_URL": f"sqlite:///{database_path}",
                "CORS_ORIGINS": "http://localhost:5173",
            },
        )
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.temp_dir.cleanup()

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"X-API-Key": self.token}

    def test_health_and_security_headers(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(200, response.status_code)
        self.assertEqual("healthy", response.get_json()["status"])
        self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
        self.assertEqual("DENY", response.headers["X-Frame-Options"])

    def test_write_requires_api_key(self) -> None:
        response = self.client.post(
            "/api/users",
            json={"username": "user", "email": "user@example.com"},
        )
        self.assertEqual(401, response.status_code)

    def test_create_list_get_update_and_delete(self) -> None:
        created = self.client.post(
            "/api/users",
            headers=self.auth_headers,
            json={"username": "User One", "email": "USER@example.com"},
        )
        self.assertEqual(201, created.status_code)
        user_id = created.get_json()["id"]
        self.assertEqual("user@example.com", created.get_json()["email"])

        listing = self.client.get("/api/users?per_page=10")
        self.assertEqual(1, listing.get_json()["pagination"]["total"])

        fetched = self.client.get(f"/api/users/{user_id}")
        self.assertEqual("User One", fetched.get_json()["username"])

        updated = self.client.patch(
            f"/api/users/{user_id}",
            headers=self.auth_headers,
            json={"username": "User Updated"},
        )
        self.assertEqual(200, updated.status_code)
        self.assertEqual("User Updated", updated.get_json()["username"])

        deleted = self.client.delete(f"/api/users/{user_id}", headers=self.auth_headers)
        self.assertEqual(204, deleted.status_code)
        self.assertEqual(404, self.client.get(f"/api/users/{user_id}").status_code)

    def test_duplicate_identity_returns_conflict(self) -> None:
        payload = {"username": "duplicate", "email": "duplicate@example.com"}
        self.assertEqual(201, self.client.post("/api/users", headers=self.auth_headers, json=payload).status_code)
        response = self.client.post("/api/users", headers=self.auth_headers, json=payload)
        self.assertEqual(409, response.status_code)

    def test_unknown_fields_are_rejected(self) -> None:
        response = self.client.post(
            "/api/users",
            headers=self.auth_headers,
            json={"username": "user", "email": "user@example.com", "role": "admin"},
        )
        self.assertEqual(400, response.status_code)

    def test_read_only_mode_returns_service_unavailable_for_writes(self) -> None:
        read_only = create_app(
            {"TESTING": True},
            environ={
                "APP_ENV": "test",
                "SECRET_KEY": "test-secret-key-with-enough-length-456",
                "DATABASE_URL": "sqlite:///:memory:",
                "CORS_ORIGINS": "http://localhost:5173",
            },
        ).test_client()
        response = read_only.post(
            "/api/users",
            json={"username": "user", "email": "user@example.com"},
        )
        self.assertEqual(503, response.status_code)


if __name__ == "__main__":
    unittest.main()

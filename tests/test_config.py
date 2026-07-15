from __future__ import annotations

import unittest

from src.config import ConfigurationError, load_settings


class ConfigTests(unittest.TestCase):
    def test_development_generates_secret_and_defaults_to_read_only(self) -> None:
        settings = load_settings({"APP_ENV": "development"})
        self.assertGreaterEqual(len(settings.secret_key), 32)
        self.assertEqual("", settings.api_write_token)

    def test_production_requires_strong_secret(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_settings({"APP_ENV": "production", "SECRET_KEY": "change-me"})

    def test_production_rejects_wildcard_cors(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_settings({
                "APP_ENV": "production",
                "SECRET_KEY": "s" * 40,
                "CORS_ORIGINS": "*",
            })

    def test_origins_are_trimmed_and_deduplicated(self) -> None:
        settings = load_settings({
            "CORS_ORIGINS": "https://a.example, https://b.example,https://a.example",
        })
        self.assertEqual(("https://a.example", "https://b.example"), settings.cors_origins)

    def test_render_postgres_url_uses_psycopg_driver(self) -> None:
        settings = load_settings({"DATABASE_URL": "postgres://user:pass@db.example/app"})
        self.assertEqual(
            "postgresql+psycopg://user:pass@db.example/app",
            settings.database_url,
        )


if __name__ == "__main__":
    unittest.main()

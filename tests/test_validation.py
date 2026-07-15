from __future__ import annotations

import unittest

from src.validation import validate_user_payload


class ValidationTests(unittest.TestCase):
    def test_valid_payload_is_normalized(self) -> None:
        cleaned, errors = validate_user_payload({
            "username": "  Abdul Basit  ",
            "email": "  USER@Example.COM ",
        })
        self.assertEqual({}, errors)
        self.assertEqual("Abdul Basit", cleaned["username"])
        self.assertEqual("user@example.com", cleaned["email"])

    def test_unknown_fields_are_rejected(self) -> None:
        cleaned, errors = validate_user_payload({
            "username": "user",
            "email": "user@example.com",
            "role": "admin",
        })
        self.assertEqual({}, cleaned)
        self.assertIn("Unknown field", errors["body"])

    def test_partial_payload_must_change_something(self) -> None:
        cleaned, errors = validate_user_payload({}, partial=True)
        self.assertEqual({}, cleaned)
        self.assertIn("At least one", errors["body"])

    def test_invalid_email_is_rejected(self) -> None:
        _cleaned, errors = validate_user_payload({"username": "user", "email": "not-email"})
        self.assertIn("email", errors)


if __name__ == "__main__":
    unittest.main()

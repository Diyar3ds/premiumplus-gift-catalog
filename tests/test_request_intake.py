from datetime import datetime, timedelta, timezone
import unittest

from src.request_intake import RequestValidationError, create_gift_request


NOW = datetime(2026, 10, 31, 18, 0, tzinfo=timezone.utc)


def sample_catalog():
    return {
        "schema_version": 2,
        "status": "ok",
        "updated_at": "2026-10-31T17:49:34Z",
        "gifts": [
            {
                "id": "1001", "title": "Heart", "emoji": "💝", "stars": 15,
                "convert_stars": 13, "auction": False, "sold_out": False,
                "is_regular_gift": True, "is_catalog_available": True,
            },
            {
                "id": "1002", "title": "Limited", "emoji": "🎁", "stars": 25,
                "convert_stars": 21, "auction": False, "sold_out": True,
                "is_regular_gift": True, "is_catalog_available": False,
            },
            {
                "id": "1003", "title": "Collectible", "emoji": "💎", "stars": 50,
                "convert_stars": 43, "auction": True, "sold_out": False,
                "is_regular_gift": False, "is_catalog_available": True,
            },
        ],
    }


class GiftRequestIntakeTests(unittest.TestCase):
    def test_creates_request_for_available_regular_gift(self):
        request = create_gift_request(
            sample_catalog(), "1001", "@Example_User", idempotency_key="tg-update-77", now=NOW
        )
        self.assertEqual(request["status"], "awaiting_authorized_owner_review")
        self.assertEqual(request["gift"]["stars_price_at_request"], 15)
        self.assertEqual(request["gift"]["reported_convert_stars"], 13)
        self.assertFalse(request["gift"]["convert_stars_is_guaranteed"])
        self.assertEqual(request["recipient"], {"kind": "username", "value": "example_user"})
        self.assertFalse(request["payment_performed"])
        self.assertFalse(request["gift_sent"])

    def test_supports_picker_user_id_as_opaque_reference(self):
        request = create_gift_request(
            sample_catalog(), "1001", 123456789, idempotency_key="tg-update-78", now=NOW
        )
        self.assertEqual(request["recipient"], {"kind": "user_id", "value": "123456789"})

    def test_rejects_stale_catalog(self):
        catalog = sample_catalog()
        catalog["updated_at"] = (NOW - timedelta(hours=8)).isoformat()
        with self.assertRaisesRegex(RequestValidationError, "stale"):
            create_gift_request(catalog, "1001", "example_user", idempotency_key="k", now=NOW)

    def test_rejects_future_catalog_timestamp(self):
        catalog = sample_catalog()
        catalog["updated_at"] = (NOW + timedelta(hours=1)).isoformat()
        with self.assertRaises(RequestValidationError):
            create_gift_request(catalog, "1001", "example_user", idempotency_key="k", now=NOW)

    def test_rejects_missing_gift(self):
        with self.assertRaisesRegex(RequestValidationError, "not found"):
            create_gift_request(sample_catalog(), "9999", "example_user", idempotency_key="k", now=NOW)

    def test_rejects_sold_out_gift(self):
        with self.assertRaisesRegex(RequestValidationError, "not globally available"):
            create_gift_request(sample_catalog(), "1002", "example_user", idempotency_key="k", now=NOW)

    def test_rejects_collectible_auction_gift(self):
        with self.assertRaisesRegex(RequestValidationError, "regular"):
            create_gift_request(sample_catalog(), "1003", "example_user", idempotency_key="k", now=NOW)

    def test_rejects_invalid_username(self):
        with self.assertRaisesRegex(RequestValidationError, "valid Telegram"):
            create_gift_request(sample_catalog(), "1001", "@xy", idempotency_key="k", now=NOW)

    def test_requires_idempotency_key(self):
        with self.assertRaisesRegex(RequestValidationError, "idempotency"):
            create_gift_request(sample_catalog(), "1001", "example_user", idempotency_key="", now=NOW)

    def test_never_creates_payment_or_send_action(self):
        request = create_gift_request(
            sample_catalog(), "1001", "example_user", idempotency_key="tg-update-80", now=NOW
        )
        self.assertEqual(request["status"], "awaiting_authorized_owner_review")
        self.assertFalse(request["payment_performed"])
        self.assertFalse(request["gift_sent"])
        self.assertTrue(request["requires_sender_specific_revalidation"])


if __name__ == "__main__":
    unittest.main()

from types import SimpleNamespace
import unittest

from src.catalog_schema import CONVERSION_NOTE, build_catalog, normalize_gift


def gift(
    gift_id: int,
    price: int,
    *,
    conversion: int,
    sold_out: bool = False,
    auction: bool = False,
    remains=None,
    per_user_remains=None,
    per_user_total=None,
    limited_per_user: bool = False,
    require_premium: bool = False,
    locked_until_date=None,
    emoji="🎁",
):
    sticker = SimpleNamespace(id=987, attributes=[SimpleNamespace(alt=emoji)])
    return SimpleNamespace(
        id=gift_id,
        title=None,
        sticker=sticker,
        stars=price,
        convert_stars=conversion,
        upgrade_stars=None,
        limited=remains is not None,
        sold_out=sold_out,
        auction=auction,
        require_premium=require_premium,
        limited_per_user=limited_per_user,
        availability_remains=remains,
        availability_total=100 if remains is not None else None,
        availability_resale=None,
        per_user_remains=per_user_remains,
        per_user_total=per_user_total,
        locked_until_date=locked_until_date,
    )


class CatalogSchemaTests(unittest.TestCase):
    def test_live_conversion_value_is_preserved_but_not_guaranteed(self):
        item = normalize_gift(gift(123, 15, conversion=13, emoji="💝"))
        self.assertEqual(item["stars"], 15)
        self.assertEqual(item["convert_stars"], 13)
        self.assertFalse(item["convert_stars_is_guaranteed"])
        self.assertEqual(item["convert_stars_note"], CONVERSION_NOTE)
        self.assertEqual(item["emoji"], "💝")

    def test_excludes_collectible_auction_gifts(self):
        data = build_catalog([
            gift(1, 15, conversion=13),
            gift(2, 50, conversion=43, auction=True),
        ])
        self.assertEqual([x["id"] for x in data["gifts"]], ["1"])

    def test_sold_out_regular_gift_remains_visible_but_unavailable(self):
        data = build_catalog([gift(3, 25, conversion=21, sold_out=True)])
        self.assertEqual(data["gift_count"], 1)
        self.assertEqual(data["available_count"], 0)
        self.assertFalse(data["gifts"][0]["is_catalog_available"])

    def test_global_stock_zero_marks_gift_unavailable(self):
        item = normalize_gift(gift(4, 50, conversion=43, remains=0))
        self.assertFalse(item["is_catalog_available"])

    def test_per_user_remains_belongs_to_catalog_identity_not_global_stock(self):
        item = normalize_gift(gift(
            5, 50, conversion=43, per_user_remains=0,
            per_user_total=1, limited_per_user=True,
        ))
        self.assertTrue(item["is_catalog_available"])
        self.assertEqual(item["per_user_remains"], 0)
        self.assertEqual(item["per_user_remains_scope"], "telegram_identity_used_to_fetch_catalogue")
        self.assertIn("sender_specific_gift_limit", item["sender_checks_required"])
        self.assertTrue(item["must_revalidate_with_actual_sender_before_purchase"])

    def test_premium_requirement_is_sender_specific_not_global_stock(self):
        item = normalize_gift(gift(6, 25, conversion=21, require_premium=True))
        self.assertTrue(item["is_catalog_available"])
        self.assertIn("sender_must_have_premium", item["sender_checks_required"])

    def test_locked_until_date_requires_sendability_check(self):
        item = normalize_gift(gift(7, 25, conversion=21, locked_until_date=1_800_000_000))
        self.assertTrue(item["is_catalog_available"])
        self.assertIn("payments.checkCanSendGift", item["sender_checks_required"])

    def test_empty_catalog_is_not_published(self):
        with self.assertRaises(RuntimeError):
            build_catalog([gift(8, 25, conversion=21, auction=True)])


if __name__ == "__main__":
    unittest.main()

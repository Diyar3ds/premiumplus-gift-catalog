from types import SimpleNamespace
import unittest

from src.catalog_schema import build_catalog, normalize_gift


def gift(gift_id: int, price: int, *, conversion: int, sold_out: bool = False,
         auction: bool = False, remains=None, per_user_remains=None, emoji="🎁"):
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
        require_premium=False,
        limited_per_user=per_user_remains is not None,
        availability_remains=remains,
        availability_total=100 if remains is not None else None,
        availability_resale=None,
        per_user_remains=per_user_remains,
        per_user_total=1 if per_user_remains is not None else None,
        locked_until_date=None,
    )


class CatalogSchemaTests(unittest.TestCase):
    def test_live_conversion_value_is_preserved(self):
        item = normalize_gift(gift(123, 15, conversion=13, emoji="💝"))
        self.assertEqual(item["stars"], 15)
        self.assertEqual(item["convert_stars"], 13)
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

    def test_limited_supply_and_per_user_limits_are_respected(self):
        sold_out = normalize_gift(gift(4, 50, conversion=43, remains=0))
        user_limited = normalize_gift(gift(5, 50, conversion=43, per_user_remains=0))
        self.assertFalse(sold_out["is_catalog_available"])
        self.assertFalse(user_limited["is_catalog_available"])

    def test_empty_catalog_is_not_published(self):
        with self.assertRaises(RuntimeError):
            build_catalog([gift(6, 25, conversion=21, auction=True)])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


CONVERSION_NOTE = (
    "Telegram-reported conversion amount, not a guaranteed payout. "
    "The amount may be lower than the gift price depending on the Stars used to buy the gift."
)


def _int_or_none(value: Any) -> int | None:
    return int(value) if value is not None else None


def sticker_emoji(document: Any) -> str | None:
    for attribute in getattr(document, "attributes", []) or []:
        alt = getattr(attribute, "alt", None)
        if alt:
            return str(alt)
    return None


def normalize_gift(gift: Any) -> dict[str, Any]:
    """Normalize a Telegram StarGift without treating bot-specific limits as global stock."""
    sticker = getattr(gift, "sticker", None)
    auction = bool(getattr(gift, "auction", False))
    sold_out = bool(getattr(gift, "sold_out", False))
    stars = int(getattr(gift, "stars"))
    remains = _int_or_none(getattr(gift, "availability_remains", None))
    per_user_remains = _int_or_none(getattr(gift, "per_user_remains", None))
    per_user_total = _int_or_none(getattr(gift, "per_user_total", None))
    locked_until_date = _int_or_none(getattr(gift, "locked_until_date", None))
    limited_per_user = bool(getattr(gift, "limited_per_user", False))
    require_premium = bool(getattr(gift, "require_premium", False))

    # This field describes the identity that fetched the catalogue (the bot),
    # not the store owner's eventual personal sender account.
    is_regular = not auction
    is_globally_available = (
        is_regular
        and not sold_out
        and stars > 0
        and (remains is None or remains > 0)
    )

    sender_checks_required: list[str] = []
    if limited_per_user:
        sender_checks_required.append("sender_specific_gift_limit")
    if require_premium:
        sender_checks_required.append("sender_must_have_premium")
    if locked_until_date is not None:
        sender_checks_required.append("payments.checkCanSendGift")

    return {
        "id": str(int(getattr(gift, "id"))),
        "title": getattr(gift, "title", None),
        "emoji": sticker_emoji(sticker) if sticker is not None else None,
        "stars": stars,
        # Retain Telegram's field as reported by the catalogue response, but
        # never present it as a guaranteed conversion amount at checkout.
        "convert_stars": int(getattr(gift, "convert_stars", 0)),
        "convert_stars_is_guaranteed": False,
        "convert_stars_note": CONVERSION_NOTE,
        "upgrade_stars": _int_or_none(getattr(gift, "upgrade_stars", None)),
        "limited": bool(getattr(gift, "limited", False)),
        "sold_out": sold_out,
        "auction": auction,
        "require_premium": require_premium,
        "limited_per_user": limited_per_user,
        "availability_remains": remains,
        "availability_total": _int_or_none(getattr(gift, "availability_total", None)),
        "availability_resale": _int_or_none(getattr(gift, "availability_resale", None)),
        "per_user_remains": per_user_remains,
        "per_user_total": per_user_total,
        "per_user_remains_scope": "telegram_identity_used_to_fetch_catalogue",
        "locked_until_date": locked_until_date,
        "sticker_document_id": str(getattr(sticker, "id")) if sticker is not None else None,
        "is_regular_gift": is_regular,
        # This reflects global catalogue supply only; it is NOT proof that a
        # particular sender can buy/send the gift to a particular recipient.
        "is_catalog_available": is_globally_available,
        "availability_scope": "global_catalogue_only",
        "sender_checks_required": sender_checks_required,
        "must_revalidate_with_actual_sender_before_purchase": True,
    }


def build_catalog(gifts: list[Any]) -> dict[str, Any]:
    normalized = [normalize_gift(gift) for gift in gifts]
    # Collectible auction gifts are not part of the ordinary Gift shop.
    regular = [gift for gift in normalized if gift["is_regular_gift"]]
    regular.sort(key=lambda item: (item["stars"], int(item["id"])))
    if not regular:
        raise RuntimeError("Telegram returned no regular Gifts; refusing to publish an empty catalogue.")

    return {
        "schema_version": 2,
        "status": "ok",
        "source": "telegram_mtproto_payments.getStarGifts",
        "catalogue_identity": "bot",
        "availability_scope": "global_catalogue_only",
        "purchase_rule": "revalidate_with_actual_sender_before_purchase",
        "conversion_note": CONVERSION_NOTE,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "gift_count": len(regular),
        "available_count": sum(1 for item in regular if item["is_catalog_available"]),
        "gifts": regular,
    }

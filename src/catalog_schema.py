from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _int_or_none(value: Any) -> int | None:
    return int(value) if value is not None else None


def sticker_emoji(document: Any) -> str | None:
    for attribute in getattr(document, "attributes", []) or []:
        alt = getattr(attribute, "alt", None)
        if alt:
            return str(alt)
    return None


def normalize_gift(gift: Any) -> dict[str, Any]:
    """Normalize Telegram's StarGift object without inventing any values."""
    sticker = getattr(gift, "sticker", None)
    auction = bool(getattr(gift, "auction", False))
    sold_out = bool(getattr(gift, "sold_out", False))
    stars = int(getattr(gift, "stars"))
    remains = _int_or_none(getattr(gift, "availability_remains", None))
    per_user_remains = _int_or_none(getattr(gift, "per_user_remains", None))

    is_regular = not auction
    is_sendable = is_regular and not sold_out and stars > 0
    if remains is not None and remains <= 0:
        is_sendable = False
    if per_user_remains is not None and per_user_remains <= 0:
        is_sendable = False

    return {
        "id": str(int(getattr(gift, "id"))),
        "title": getattr(gift, "title", None),
        "emoji": sticker_emoji(sticker) if sticker is not None else None,
        "stars": stars,
        "convert_stars": int(getattr(gift, "convert_stars", 0)),
        "upgrade_stars": _int_or_none(getattr(gift, "upgrade_stars", None)),
        "limited": bool(getattr(gift, "limited", False)),
        "sold_out": sold_out,
        "auction": auction,
        "require_premium": bool(getattr(gift, "require_premium", False)),
        "limited_per_user": bool(getattr(gift, "limited_per_user", False)),
        "availability_remains": remains,
        "availability_total": _int_or_none(getattr(gift, "availability_total", None)),
        "availability_resale": _int_or_none(getattr(gift, "availability_resale", None)),
        "per_user_remains": per_user_remains,
        "per_user_total": _int_or_none(getattr(gift, "per_user_total", None)),
        "locked_until_date": _int_or_none(getattr(gift, "locked_until_date", None)),
        "sticker_document_id": str(getattr(sticker, "id")) if sticker is not None else None,
        "is_regular_gift": is_regular,
        "is_catalog_available": is_sendable,
    }


def build_catalog(gifts: list[Any]) -> dict[str, Any]:
    normalized = [normalize_gift(gift) for gift in gifts]
    # Collectible auction gifts are not part of the ordinary Gift shop.
    regular = [gift for gift in normalized if gift["is_regular_gift"]]
    regular.sort(key=lambda item: (item["stars"], int(item["id"])))
    if not regular:
        raise RuntimeError("Telegram returned no regular Gifts; refusing to publish an empty catalogue.")

    return {
        "schema_version": 1,
        "status": "ok",
        "source": "telegram_mtproto_payments.getStarGifts",
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "gift_count": len(regular),
        "available_count": sum(1 for item in regular if item["is_catalog_available"]),
        "gifts": regular,
    }

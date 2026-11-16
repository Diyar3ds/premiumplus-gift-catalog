"""Safe, read-only intake validation for regular Telegram Gift requests.

This module never creates a Telegram payment form, spends Stars, or sends a Gift.
Requests created here must be stored in the store bot's private database, never
in this public repository.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
import uuid
from typing import Any


CATALOG_SCHEMA_VERSION = 2
DEFAULT_MAX_CATALOG_AGE = timedelta(hours=7)
USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")


class RequestValidationError(ValueError):
    """Raised when a catalogue or requested Gift cannot safely be used."""


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError("Catalogue timestamp is missing.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RequestValidationError("Catalogue timestamp is invalid.") from exc
    if parsed.tzinfo is None:
        raise RequestValidationError("Catalogue timestamp must include a timezone.")
    return parsed.astimezone(timezone.utc)


def validate_catalog_freshness(
    catalog: dict[str, Any],
    *,
    now: datetime | None = None,
    max_age: timedelta = DEFAULT_MAX_CATALOG_AGE,
) -> datetime:
    """Validate feed shape and freshness; return its UTC updated_at value."""
    if not isinstance(catalog, dict):
        raise RequestValidationError("Catalogue must be a JSON object.")
    if catalog.get("schema_version") != CATALOG_SCHEMA_VERSION:
        raise RequestValidationError("Unsupported catalogue schema version.")
    if catalog.get("status") != "ok":
        raise RequestValidationError("Catalogue is not in an OK state.")
    if not isinstance(catalog.get("gifts"), list):
        raise RequestValidationError("Catalogue gifts field is invalid.")

    updated_at = _parse_utc(catalog.get("updated_at"))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = current - updated_at
    if age < timedelta(minutes=-5):
        raise RequestValidationError("Catalogue timestamp is unexpectedly in the future.")
    if age > max_age:
        raise RequestValidationError("Catalogue is stale; refresh it before accepting a request.")
    return updated_at


def normalize_recipient(value: str | int) -> dict[str, str]:
    """Normalize an @username or a Telegram user ID obtained from a picker.

    User IDs are stored as opaque references. A sender-side client must resolve
    them in its own Telegram session; access_hash values are never copied from
    another session or stored here.
    """
    if isinstance(value, bool):
        raise RequestValidationError("Recipient reference is invalid.")
    if isinstance(value, int):
        if value <= 0 or value > 0xFFFFFFFFFF:
            raise RequestValidationError("Telegram user ID is outside the valid range.")
        return {"kind": "user_id", "value": str(value)}

    if not isinstance(value, str):
        raise RequestValidationError("Recipient must be a username or user ID.")
    username = value.strip()
    if username.startswith("@"):
        username = username[1:]
    if not USERNAME_RE.fullmatch(username):
        raise RequestValidationError("Enter a valid Telegram @username.")
    return {"kind": "username", "value": username.lower()}


def create_gift_request(
    catalog: dict[str, Any],
    gift_id: str | int,
    recipient: str | int,
    *,
    idempotency_key: str,
    now: datetime | None = None,
    max_catalog_age: timedelta = DEFAULT_MAX_CATALOG_AGE,
) -> dict[str, Any]:
    """Create a non-payment request intent from a fresh, public Gift catalogue.

    The caller must persist idempotency_key under a UNIQUE constraint in the
    private Tbot database to prevent duplicate Telegram updates from creating
    multiple requests. Customer data must never be pushed to the public repo.
    """
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise RequestValidationError("A stable idempotency key is required.")
    if len(idempotency_key) > 200:
        raise RequestValidationError("Idempotency key is too long.")

    updated_at = validate_catalog_freshness(catalog, now=now, max_age=max_catalog_age)
    recipient_ref = normalize_recipient(recipient)
    wanted_id = str(gift_id).strip()
    if not wanted_id.isdigit():
        raise RequestValidationError("Gift ID must be a numeric Telegram identifier.")

    gift = next((item for item in catalog["gifts"] if str(item.get("id")) == wanted_id), None)
    if gift is None:
        raise RequestValidationError("Gift ID was not found in the latest catalogue.")
    if gift.get("auction") or not gift.get("is_regular_gift"):
        raise RequestValidationError("Only regular, non-auction Gifts can be requested here.")
    if gift.get("sold_out") or not gift.get("is_catalog_available"):
        raise RequestValidationError("This Gift is not globally available in the latest catalogue.")

    stars = gift.get("stars")
    if isinstance(stars, bool) or not isinstance(stars, int) or stars <= 0:
        raise RequestValidationError("Gift price in Stars is invalid.")

    reported_conversion = gift.get("convert_stars")
    if isinstance(reported_conversion, bool) or not isinstance(reported_conversion, int) or reported_conversion < 0:
        raise RequestValidationError("Telegram-reported conversion value is invalid.")

    created_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return {
        "request_id": uuid.uuid4().hex,
        "idempotency_key": idempotency_key,
        "request_type": "regular_telegram_gift",
        "status": "awaiting_authorized_owner_review",
        "created_at": created_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "catalogue_updated_at": updated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "gift": {
            "id": wanted_id,
            "title": gift.get("title"),
            "emoji": gift.get("emoji"),
            "stars_price_at_request": stars,
            "reported_convert_stars": reported_conversion,
            "convert_stars_is_guaranteed": False,
        },
        "recipient": recipient_ref,
        "requires_sender_specific_revalidation": True,
        "payment_performed": False,
        "gift_sent": False,
    }

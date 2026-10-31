from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from telethon import TelegramClient, functions
from telethon.sessions import StringSession

from .catalog_schema import build_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "gifts.json"


def build_bot_client() -> TelegramClient:
    """Create an ephemeral MTProto bot session; no personal-user session is used."""
    api_id_raw = os.environ.get("TELEGRAM_API_ID", "").strip()
    api_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not api_id_raw or not api_hash or not bot_token:
        raise RuntimeError("Missing Telegram bot catalogue secrets.")
    try:
        api_id = int(api_id_raw)
    except ValueError as exc:
        raise RuntimeError("TELEGRAM_API_ID must be an integer.") from exc
    # StringSession keeps authorization in memory only; no .session file is written.
    return TelegramClient(StringSession(), api_id, api_hash)


def write_catalog(catalog: dict[str, Any], path: Path = CATALOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="gifts-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(catalog, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


async def sync_catalog() -> dict[str, Any]:
    client = build_bot_client()
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    try:
        await client.start(bot_token=bot_token)
        me = await client.get_me()
        if me is None or not bool(getattr(me, "bot", False)):
            raise RuntimeError("The configured Telegram identity is not a bot; refusing to continue.")

        response = await client(functions.payments.GetStarGiftsRequest(hash=0))
        gifts = getattr(response, "gifts", None)
        if gifts is None:
            raise RuntimeError("Telegram returned no full Gift list.")

        catalog = build_catalog(list(gifts))
        write_catalog(catalog)
        return catalog
    finally:
        if client.is_connected():
            await client.disconnect()


if __name__ == "__main__":
    try:
        result = asyncio.run(sync_catalog())
    except Exception as exc:
        # Public Actions logs must never include exception details or credentials.
        print(f"Catalogue sync failed ({exc.__class__.__name__}); previous JSON was preserved.")
        raise SystemExit(1)
    print(
        "Catalogue refreshed: "
        f"{result['available_count']} available / {result['gift_count']} regular Gifts."
    )

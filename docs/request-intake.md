# Gift request intake contract (no payment or dispatch)

This module defines the safe hand-off between a Telegram bot UI and its private order database.

## Request lifecycle

1. Read the public `data/gifts.json` catalogue.
2. Reject unsupported, stale, malformed or non-`ok` catalogues.
3. Resolve the selected `gift_id` only against a globally available regular Gift.
4. Validate the recipient reference as an `@username` or positive Telegram user ID supplied by a picker.
5. Create one request intent with status `awaiting_authorized_owner_review`.
6. Persist the request in the store bot's private SQLite database, using a UNIQUE constraint on `idempotency_key`.

## Privacy and safety boundaries

- Never write customer IDs, usernames, requests, payment information, or order history to this public repository.
- Never store Telegram access hashes in the request record. Access hashes are session-specific; a sender client must resolve the recipient in its own session if a later authorized workflow requires it.
- The request record preserves the displayed Stars price and Telegram-reported conversion value as a snapshot only. It does not guarantee availability or conversion at a later time.
- Before any future fulfillment, an authorized account owner must independently re-check sender eligibility, recipient acceptance restrictions, current price and availability.
- This module contains no payment-form creation, Stars spending, Gift purchase, Gift dispatch, refund, or personal-account session code.
- The `idempotency_key` must be stable across retries of the same incoming Telegram update and protected by a database UNIQUE constraint. The function itself does not replace database-level deduplication.

## Freshness

The default catalogue acceptance window is seven hours, matching the current six-hour scheduled sync with a one-hour margin. This check only protects against an obviously stale feed; it does not reserve a Gift or prove that a sender can purchase it.

import unittest

import telethon
from telethon import functions, types


class TelethonMtprotoCompatibilityTests(unittest.TestCase):
    def test_pinned_telethon_version(self):
        self.assertEqual(telethon.__version__, "1.45.0")

    def test_catalog_request_is_available(self):
        request = functions.payments.GetStarGiftsRequest(hash=0)
        self.assertEqual(request.hash, 0)

    def test_regular_gift_invoice_and_payment_requests_are_available(self):
        invoice = types.InputInvoiceStarGift(
            peer=types.InputPeerSelf(),
            gift_id=123,
        )
        payment_form = functions.payments.GetPaymentFormRequest(invoice=invoice)
        submit_form = functions.payments.SendStarsFormRequest(
            form_id=1,
            invoice=invoice,
        )
        self.assertEqual(payment_form.invoice, invoice)
        self.assertEqual(submit_form.invoice, invoice)

    def test_personal_sender_precheck_method_is_available(self):
        # Telegram documents this method for users only. The bot catalogue job
        # must not call it; a future sender-side flow must use the actual sender.
        request = functions.payments.CheckCanSendGiftRequest(gift_id=123)
        self.assertEqual(request.gift_id, 123)


if __name__ == "__main__":
    unittest.main()

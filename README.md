# Premium Plus+ — Telegram Gift Catalogue

این مخزن، سرویس مستقل و فقط‌خواندنی کاتالوگ Giftهای عادی تلگرام برای Premium Plus+ است.

## هدف اصلی فروشگاه

هدف محصول نهایی، فروش Gift معمولی تلگرام (نه Gift کلکسیونی/Marketplace) است؛ مشتری گیرنده را انتخاب می‌کند و Gift باید به همان گیرنده برسد. برای هر Gift باید شناسهٔ واقعی تلگرام (`id`)، قیمت جاری (`stars`)، مقدار گزارش‌شدهٔ تبدیل (`convert_stars`)، شرایط Premium و محدودیت موجودی بررسی شوند.

کاتالوگ با MTProto و `payments.getStarGifts` خوانده می‌شود. تلگرام این متد را برای ربات و کاربر مستند کرده است؛ بنابراین این مرحله با هویت ربات انجام می‌شود و Session حساب شخصی لازم ندارد.

## تفاوت مسیرهای ارسال

- Bot API متد `sendGift` را دارد، اما مستندات رسمی می‌گویند Gift ارسالی از این متد توسط گیرنده قابل تبدیل به Stars نیست.
- MTProto مسیر جداگانهٔ `inputInvoiceStarGift`، `payments.getPaymentForm` و `payments.sendStarsForm` را دارد. مستندات فعلی `getPaymentForm` و `sendStarsForm` را برای ربات و کاربر فهرست می‌کنند.
- این تفاوت به‌تنهایی تضمین نمی‌کند هر Gift خریداری‌شده با هویت ربات MTProto در عمل دقیقاً همان قابلیت تبدیل را داشته باشد. پیش از انتخاب مسیر ارسال برای فروش واقعی، باید این رفتار با حساب/ربات مجاز و بدون خرج‌کردن ناخواسته بررسی شود.
- `payments.checkCanSendGift` در مستندات تلگرام فقط برای کاربران است. بنابراین کاتالوگ ربات نباید نتیجهٔ آن را جعل یا شبیه‌سازی کند؛ شرایط اختصاصی فرستنده باید با هویت واقعی فرستنده بررسی شود.

## اطلاعات قیمت و تبدیل

`stars` قیمت اعلام‌شدهٔ Gift در کاتالوگ است. `convert_stars` مقدار گزارش‌شده توسط تلگرام است، اما تضمین مبلغ دریافتی گیرنده نیست؛ تلگرام توضیح می‌دهد مقدار تبدیل می‌تواند بسته به زمان خرید Stars مصرف‌شده کمتر از قیمت Gift باشد. تبدیل فقط در بازهٔ زمانی مجاز تلگرام و در صورت غیرصفر بودن مقدار تبدیل ممکن است.

## اجزای مخزن

- `src/catalog.py`: اتصال MTProto فقط با Bot Token و خواندن کاتالوگ
- `src/catalog_schema.py`: نرمال‌سازی و فیلتر Giftهای معمولی؛ بدون شبکه و قابل تست
- `data/gifts.json`: خروجی عمومی کاتالوگ
- `.github/workflows/sync-catalog.yml`: اجرای دستی یا زمان‌بندی‌شده هر ۶ ساعت
- `.github/workflows/tests.yml`: تست منطق کاتالوگ و سازگاری کلاس‌های MTProto

## GitHub Actions Secrets

در **Settings → Secrets and variables → Actions** این سه Secret را بساز. مقادیر را در فایل‌ها، Issues، Pull Request یا گفتگو قرار نده:

| Secret | کاربرد |
|---|---|
| `TELEGRAM_API_ID` | API ID اپ تلگرام |
| `TELEGRAM_API_HASH` | API Hash همان اپ |
| `TELEGRAM_BOT_TOKEN` | توکن ربات کاتالوگ |

Workflow کاتالوگ فقط به این مقادیر برای خواندن دادهٔ عمومی Gift نیاز دارد. GitHub Token فقط در مرحلهٔ انتشار JSON به کار می‌رود و هنگام نصب پکیج‌ها در محیط در دسترس نیست.

## اجرا

1. سه Secret بالا را اضافه کن.
2. Pull Request را بررسی کن و پس از تأیید، آن را به `main` ادغام کن.
3. در تب **Actions**، Workflow با نام **Sync Telegram Gift Catalogue** را از `Run workflow` یک بار دستی اجرا کن.
4. پس از اجرای موفق، `data/gifts.json` با دادهٔ واقعی تلگرام به‌روزرسانی می‌شود.
5. پس از آن Workflow طبق زمان‌بندی هر ۶ ساعت اجرا خواهد شد.

## قواعد کاتالوگ

- Giftهای دارای `auction=true` از فهرست فروش عادی کنار گذاشته می‌شوند.
- Giftهای تمام‌شده می‌توانند برای نمایش باقی بمانند، ولی `is_catalog_available=false` خواهند داشت.
- `per_user_remains` به هویت تلگرامی‌ای تعلق دارد که کاتالوگ را دریافت کرده است (در این پروژه ربات) و معادل موجودی عمومی نیست.
- محدودیت Premium، محدودیت هر فرستنده و `locked_until_date` باید برای فرستندهٔ واقعی دوباره بررسی شوند.
- اگر تلگرام فهرست خالی یا بدون Gift عادی بدهد، فایل قبلی overwrite نمی‌شود.
- خروجی عمومی فقط شامل دادهٔ عمومی Giftها است؛ نه username مشتری، user_id، سفارش یا دادهٔ خصوصی.

## منابع رسمی

- Telegram Gifts: https://core.telegram.org/api/gifts
- `payments.getStarGifts`: https://core.telegram.org/method/payments.getStarGifts
- `payments.checkCanSendGift`: https://core.telegram.org/method/payments.checkCanSendGift
- `payments.getPaymentForm`: https://core.telegram.org/method/payments.getPaymentForm
- `payments.sendStarsForm`: https://core.telegram.org/method/payments.sendStarsForm
- Bot API `sendGift`: https://core.telegram.org/bots/api#sendgift

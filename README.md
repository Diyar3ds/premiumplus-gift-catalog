# Premium Plus+ — Telegram Gift Catalogue

این مخزن، سرویس مستقل و فقط‌خواندنی کاتالوگ Giftهای عادی تلگرام برای Premium Plus+ است.

## هدف اصلی پروژه

هدف نهایی فروشگاه، فروش **Gift معمولی تلگرام** (نه Gift کلکسیونی/Marketplace) به گیرنده‌ای است که مشتری مشخص می‌کند. طرح اصلی فروشگاه این است که Gift در نهایت از حساب شخصی صاحب فروشگاه ارسال شود؛ این مخزن فعلاً فقط کاتالوگ زنده و پایهٔ داده را فراهم می‌کند و خودش Gift نمی‌خرد یا ارسال نمی‌کند.

کاتالوگ با MTProto و `payments.getStarGifts` خوانده می‌شود. شناسهٔ تلگرام (`id`) کلید اصلی هر Gift است؛ ایموجی یا نام آن شناسهٔ یکتا نیست.

## نکات مهم صحت داده

- `stars` قیمت اعلام‌شدهٔ Gift در کاتالوگ تلگرام است.
- `convert_stars` مقدار conversion گزارش‌شده توسط تلگرام است، نه تضمین مقدار دریافتی نهایی. طبق مستندات تلگرام، این مقدار فقط وقتی با قیمت Gift برابر است که Gift با Stars تازه‌خریداری‌شده تهیه شود؛ در غیر این صورت می‌تواند کمتر باشد.
- `per_user_remains` ظرفیت باقی‌مانده برای **همان هویتی** است که کاتالوگ را دریافت کرده است. این نسخه کاتالوگ را با هویت ربات می‌گیرد؛ بنابراین این مقدار برای حساب شخصی فرستنده قابل تعمیم نیست و در دسترس‌بودن عمومی Gift دخالت داده نمی‌شود.
- موجودی کلی (`availability_remains`) و وضعیت `sold_out` برای تشخیص عرضهٔ عمومی استفاده می‌شوند.
- محدودیت Premium، سقف هر کاربر و `locked_until_date` باید با هویت واقعی فرستنده در زمان خرید بررسی شوند. اگر `locked_until_date` وجود داشته باشد، مستندات تلگرام استفاده از `payments.checkCanSendGift` را برای بررسی امکان ارسال توصیه می‌کند.
- `is_catalog_available` فقط وضعیت عرضهٔ عمومی را بیان می‌کند؛ تضمین نمی‌کند حساب فرستنده یا گیرنده برای سفارش خاص واجد شرایط باشد.
- Giftهای مزایده‌ای/کلکسیونی از کاتالوگ فروش Gift عادی کنار گذاشته می‌شوند.

## اجزای مخزن

- `src/catalog.py`: اتصال MTProto فقط با Bot Token و خواندن کاتالوگ
- `src/catalog_schema.py`: نرمال‌سازی اطلاعات Giftها بدون شبکه
- `data/gifts.json`: خروجی عمومی کاتالوگ
- `.github/workflows/sync-catalog.yml`: اجرای دستی یا زمان‌بندی‌شدهٔ همگام‌سازی
- `.github/workflows/tests.yml`: تست‌های واحد

## GitHub Actions Secrets

در **Settings → Secrets and variables → Actions** این سه Secret را تعریف کن:

| Secret | کاربرد |
|---|---|
| `TELEGRAM_API_ID` | API ID اپ تلگرام |
| `TELEGRAM_API_HASH` | API Hash همان اپ |
| `TELEGRAM_BOT_TOKEN` | توکن ربات کاتالوگ |

مقادیر واقعی را داخل فایل‌های مخزن، Issues، کد عمومی یا لاگ‌ها قرار نده. `.env.example` فقط نمونهٔ خالی است. Session حساب شخصی نباید در مخزن Public قرار بگیرد.

## اجرا

1. سه Secret بالا را اضافه کن.
2. در تب **Actions**، Workflow با نام **Sync Telegram Gift Catalogue** را از `Run workflow` اجرا کن.
3. پس از موفقیت، `data/gifts.json` با دادهٔ واقعی کاتالوگ به‌روز می‌شود.
4. زمان‌بندی فعلی Workflow هر ۶ ساعت است.

## منابع رسمی

- Telegram Gifts: https://core.telegram.org/api/gifts
- StarGift constructor: https://core.telegram.org/constructor/starGift
- `payments.getStarGifts`: https://core.telegram.org/method/payments.getStarGifts
- `payments.checkCanSendGift`: https://core.telegram.org/method/payments.checkCanSendGift

# Premium Plus+ — Telegram Gift Catalogue

این مخزن، سرویس مستقل و فقط‌خواندنی کاتالوگ Giftهای عادی تلگرام برای Premium Plus+ است.

## اصل پروژه

هدف نهایی فروشگاه، Gift معمولی تلگرام است (نه Gift کلکسیونی/Marketplace). اطلاعات کاتالوگ باید زنده باشد و برای هر Gift حداقل این موارد ثبت شوند:

- شناسهٔ واقعی تلگرام (`id`)؛ نه اتکا به ایموجی یا اسم
- قیمت لحظه‌ای به Stars (`stars`)
- مقدار واقعی تبدیل به Stars (`convert_stars`)
- ایموجی/استیکر، محدودیت موجودی، تعداد باقی‌مانده و شرط Premium
- وضعیت موجود/ناموجود بودن Gift

کاتالوگ از MTProto با `payments.getStarGifts` خوانده می‌شود. طبق مستندات رسمی تلگرام، این متد برای **کاربر و ربات** در دسترس است؛ بنابراین این مرحله با هویت ربات انجام می‌شود و هیچ Session یا ورود حساب شخصی لازم ندارد. `convert_stars` هم از فیلد واقعی StarGift خوانده می‌شود و برای قیمت‌های ۱۵/۲۵/۵۰/۱۰۰ هیچ عددی hardcode نشده است.

این مخزن در این مرحله **هیچ Giftی نمی‌خرد و ارسال نمی‌کند**. پرداخت یا ارسال از حساب شخصی صاحب فروشگاه مرحله‌ای جداگانه است و باید توسط خود صاحب‌حساب بالغ، با رعایت شرایط و قوانین تلگرام بررسی و مدیریت شود. هیچ اعتبارنامه یا Session شخصی در این مخزن قرار نمی‌گیرد.

## اجزای مخزن

- `src/catalog.py`: اتصال MTProto فقط با Bot Token، خواندن کاتالوگ، انتشار JSON
- `src/catalog_schema.py`: نرمال‌سازی و فیلتر Giftهای معمولی؛ بدون شبکه و قابل تست
- `data/gifts.json`: خروجی عمومی کاتالوگ
- `.github/workflows/sync-catalog.yml`: اجرای دستی یا خودکار هر ۶ ساعت
- `.github/workflows/tests.yml`: تست خودکار منطق کاتالوگ

## GitHub Actions Secrets

در **Settings → Secrets and variables → Actions** این سه Secret را بساز:

| Secret | کاربرد |
|---|---|
| `TELEGRAM_API_ID` | API ID اپ تلگرام |
| `TELEGRAM_API_HASH` | API Hash همان اپ |
| `TELEGRAM_BOT_TOKEN` | توکن ربات فروشگاه |

این مقادیر را داخل فایل‌ها، Issues، کد عمومی یا گفتگو منتشر نکن. Workflow فقط آن‌ها را به فرایند کاتالوگ می‌دهد. از Bot Token اختصاصی مناسب این پروژه استفاده کن؛ توکن‌های خصوصی دیگر را در مخزن نگذار.

## اجرا

1. سه Secret بالا را اضافه کن.
2. به تب **Actions** برو.
3. Workflow با نام **Sync Telegram Gift Catalogue** را از `Run workflow` یک بار دستی اجرا کن.
4. پس از اجرای موفق، فایل `data/gifts.json` با دادهٔ واقعی تلگرام به‌روزرسانی می‌شود.
5. بعد از آن workflow طبق زمان‌بندی هر ۶ ساعت اجرا می‌شود.

## نمونهٔ ساختار خروجی

```json
{
  "schema_version": 1,
  "status": "ok",
  "source": "telegram_mtproto_payments.getStarGifts",
  "updated_at": "UTC timestamp from the run",
  "gift_count": 1,
  "available_count": 1,
  "gifts": [
    {
      "id": "telegram-gift-id",
      "emoji": "🎁",
      "stars": 15,
      "convert_stars": 13,
      "is_regular_gift": true,
      "is_catalog_available": true
    }
  ]
}
```

مقادیر بالا فقط نمونهٔ شکل داده‌اند، نه قیمت یا شناسهٔ فعلی تلگرام.

## قواعد کاتالوگ

- Giftهای دارای `auction=true` از فهرست فروش عادی کنار گذاشته می‌شوند.
- Giftهای تمام‌شده می‌توانند برای نمایش در کاتالوگ بمانند، ولی `is_catalog_available=false` خواهند داشت.
- محدودیت موجودی کلی و محدودیت خرید هر کاربر در وضعیت موجود بودن لحاظ می‌شود.
- اگر تلگرام فهرست خالی یا بدون Gift عادی بدهد، فایل قبلی overwrite نمی‌شود.
- کاتالوگ عمومی شامل اطلاعات عمومی Giftها است؛ نه username مشتری، user_id، سفارش یا دادهٔ خصوصی.

## منابع رسمی

- Telegram Gifts: https://core.telegram.org/api/gifts
- `payments.getStarGifts`: https://core.telegram.org/method/payments.getStarGifts
- StarGift fields: https://core.telegram.org/constructor/starGift

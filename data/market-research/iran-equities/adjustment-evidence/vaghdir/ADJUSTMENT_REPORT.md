# گزارش تعدیل وغدیر (Vaghdir Adjustment Report)

**تاریخ:** ۱۴۰۵-۰۸-۲۶ (2026-11-17)
**وضعیت:** 🟡 در حال بررسی — پذیرش نهایی صادر نشده

## منابع داده

| منبع | فایل | تعداد رکورد |
|---|---|---|
| TSETMC GetPriceAdjustList | raw/tsetmc/vaghdir_price_adjust_raw.json | ۲۵ |
| TSETMC GetInstrumentShareChange | raw/tsetmc/vaghdir_share_change_raw.json | ۷ |
| iranquant adjusted_all | raw/vaghdir_adjusted_all.csv | ۵۳۸۶ روز |
| iranquant events | validation/vaghdir_events_estimated.csv | ۲۲ رویداد |
| تطبیق TSETMC vs iranquant | validation/tsetmc_vs_iranquant_comparison.csv | — |

## رویدادهای تأییدشده (وجود سند)

| تاریخ | نوع | درصد | سند | وضعیت ضریب |
|---|---|---|---|---|
| 2024-09-09 | افزایش سرمایه | ۲۰۰٪ | کدال (آگهی ثبت) | ✅ تأیید شد |
| 2013-02-27 | سود نقدی | ۱۰.۸٪ | کدال (۱۰۵۲۴۳) | 🟡 وجود تأیید، ضریب مستقل تأیید نشده |
| 2015-03-17 | سود نقدی | ۱۶.۳٪ | کدال (۲۰۲۳۲۷) | 🟡 وجود تأیید، ضریب مستقل تأیید نشده |
| 2011-04-26 | ترکیبی | ۹۷.۵۳٪ + سود | کدال (۳۸۴۴۸) + TSETMC | 🟡 چهار رکورد مستقل؛ ترتیب اعمال حل‌نشده |
| 2010-04-21 | نامشخص | ۱۱.۲٪ | ❌ بدون سند | 🔴 قرنطینه |

## اصلاح مهم

- «اطلاعیه سود پیدا شد» با «ضریب تعدیل اثبات شد» دو وضعیت متفاوت‌اند.
- چهار رکورد ۲۰۱۱ نباید در یک مقدار ترکیبی ادغام شوند؛ هر رکورد شناسه، ضریب و وضعیت مستقل دارد.
- `investment_outputs_default: DISABLED` طبق `RELEASE_GATES.json` — تا تکمیل `RG-03` و `RG-04`، این داده‌ها فقط پژوهشی هستند.

## اقدامات باقی‌مانده

1. تطبیق مستقل ضرایب ۲۰۱۳ و ۲۰۱۵ (آیا 0.892 و 0.837 دقیقاً از سود نقدی ناشی شده‌اند؟)
2. بازسازی ترتیب اعمال ۴ رکورد ۲۰۱۱
3. تصمیم درباره ۲۰۱۰ (پذیرش با احتیاط یا قرنطینه دائم)
4. تکمیل `RG-03` (Data trust) و `RG-04` (Analytical validity) قبل از هر استفاده تحلیلی

## وضعیت حاکمیتی

این گزارش زیر تسک `MS-DATA-001` (Market coverage and canonical instrument registry) ثبت می‌شود.

طبق `RELEASE_GATES.json`:
- `RG-03` (Data trust): ❌ هنوز رد نشده — حقوق استفاده، تطبیق مستقل قیمت و صحت corporate-action تأیید نشده‌اند.
- `RG-04` (Analytical validity): ❌ هنوز رد نشده — point-in-time inputs و walk-forward تأیید نشده‌اند.
- `investment_outputs_default: DISABLED` — این داده‌ها فقط پژوهشی هستند و نباید در سایت یا بک‌تست استفاده شوند.

**هیچ‌کدام از این ۷ رویداد نباید به عنوان «تأیید نهایی» در نظر گرفته شوند.** حداکثر وضعیت، `READY` برای بررسی بیشتر است، نه `ACCEPTED`.

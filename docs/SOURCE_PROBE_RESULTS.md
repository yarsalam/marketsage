# نتایج نخستین probe منابع MarketSage

- work_id: MS-BATCH-DATA-PIPELINE-20261119-01
- workflow: https://github.com/yarsalam/marketsage/actions/runs/44555538334
- artifact: marketsage-source-probe-68d0980c5b5916247a0e3784f6cf4f1855d72377
- زمان اجرا: 2026-11-19 15:30:31 تا 15:31:10 UTC
- محیط: GitHub-hosted Ubuntu 26.04، منطقهٔ westus3
- سیاست: GETهای کم‌حجم؛ حداکثر 256 KiB از هر پاسخ؛ payload خام در مخزن ذخیره نشده؛ فقط hash و خلاصهٔ schema در artifact قرار دارد.

## نتیجه

| منبع | نتیجهٔ HTTP | شواهد | تصمیم فعلی |
|---|---:|---|---|
| TSETMC search | 200 | JSON معتبر؛ 41 نتیجه برای جست‌وجوی «فولاد»؛ کلیدهای instrumentSearch و insCode و lVal18AFC موجود | قابل دسترسی از runner ابری؛ هنوز تاریخچه و رویدادها probe نشده‌اند. |
| TGJU history | 200 | پاسخ JSON از سقف probe یعنی 256 KiB بزرگ‌تر بود؛ hash پاسخ ثبت شد اما parse کامل انجام نشد | endpoint پاسخ می‌دهد؛ باید DataTables pagination با start/length استفاده شود و دادهٔ خام کامل جداگانه دریافت شود. |
| NerkhAra index | 200 | JSON معتبر، 14,366 بایت؛ کلیدهای api, attribution, by_day_years, documentation, endpoints, ids, terms و units موجود | index قابل دریافت است؛ باید شناسهٔ نمادها، terms و تاریخچهٔ نمونه بررسی شوند. |
| NetArz currencies | 401 | Unauthorized | بدون API key قابل استفاده نیست؛ تا تأمین کلید و بررسی پلن، adapter غیرفعال می‌ماند. |
| Nobitex market stats | 200 | JSON معتبر، 359 بایت؛ کلیدهای status, stats و global موجود | دسترسی عمومی تأیید شد؛ endpoint تاریخچهٔ OHLC هنوز باید جداگانه probe شود. |
| Wallex markets | 200 | پاسخ از سقف 256 KiB بزرگ‌تر بود؛ hash ثبت شد اما parse کامل انجام نشد | endpoint پاسخ می‌دهد؛ باید schema/فهرست بازار با parser جریانی یا پاسخ محدود بررسی شود. |
| Alpha Vantage daily | 200 | JSON معتبر، 21,300 بایت؛ کلیدهای Meta Data و Time Series (Daily) | endpoint مستند و قابل دسترسی با demo key برای IBM؛ محدودیت free tier و adjusted endpoint هنوز بررسی نشده است. |

خلاصه: ۷ endpoint بررسی شد؛ ۴ پاسخ در محدودهٔ parse، ۲ پاسخ بزرگ‌تر از سقف probe و ۱ پاسخ 401. این اعداد به معنی پذیرش ۷ منبع نیستند.

## شواهد تکمیلی مستندات

### TSETMC
کاتالوگ endpoint عمومی، جست‌وجوی ابزار، تاریخچهٔ روزانه و endpointهای رویداد را شرح می‌دهد. همان کاتالوگ هشدار می‌دهد که GetClosingPriceDailyList ممکن است برای بسیاری از ابزارها خالی باشد؛ endpoint قدیمی InstTradeHistory.aspx نیز برای تاریخچهٔ معاملات معرفی شده است. بنابراین adapter باید fallback و مقایسهٔ پوشش داشته باشد؛ صرف HTTP 200 کافی نیست.

### TGJU
کد مستقل استفاده‌کننده از endpoint، ساختار DataTables را با start و length و ۸ ستون نشان می‌دهد؛ بنابراین دریافت صفحه‌ای ممکن است و پاسخ کامل نباید در probe محدود 256 KiB خوانده شود. کد نمونهٔ ثالث OHLC را دستکاری می‌کند؛ MarketSage نباید این پاک‌سازی را روی raw اعمال کند. دادهٔ خام TGJU باید بدون تغییر ذخیره شود و ناسازگاری OHLC به quality issue تبدیل شود، نه clamp خاموش.

### FIPIRAN
کد wrapper عمومی، base service را برابر https://www.fipiran.com/services/ نشان می‌دهد. endpoint تاریخچهٔ NAV به شکل chart/getfundchart?regno=...&showAll=true و فیلدهای issueNav، cancelNav، statisticalNav و date مستند شده‌اند. endpoint فهرست صندوق‌ها fund/fundcompare/ است. این‌ها شواهد فنی ثالث‌اند و هنوز مجوز و پوشش مستقیم تأیید نشده‌اند.

### Wallex و Nobitex
مستند رسمی Wallex مسیر OHLC را /v1/udf/history با symbol، resolution، from و to معرفی می‌کند و بازارها را با /v1/markets فهرست می‌کند. مستند Nobitex مسیر OHLC را /market/udf/history معرفی می‌کند و حداکثر ۵۰۰ کندل در هر پاسخ را شرح می‌دهد؛ بنابراین pagination ضروری است.

## محدودیت‌های probe
- از پاسخ‌های بزرگ TGJU و Wallex فقط 256 KiB خوانده شد؛ hash ثبت‌شده hash همان بخش خوانده‌شده است، نه کل پاسخ.
- هیچ دادهٔ کامل تاریخی ذخیره نشده است.
- TSETMC، FIPIRAN، TGJU، NerkhAra، Nobitex، Wallex و Alpha Vantage هنوز برای استفادهٔ تحلیلی نهایی پذیرفته نشده‌اند.
- بررسی مجوز/حق بازتوزیع و تست پوشش تاریخی هنوز باز است.
- probe از GitHub-hosted runner انجام شد؛ دسترسی این محیط، دسترسی همهٔ محیط‌های اجرایی را تضمین نمی‌کند.

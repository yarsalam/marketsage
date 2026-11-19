# وضعیت رسمی پروژه MarketSage

- شناسهٔ کار جاری: `MS-BATCH-DATA-PIPELINE-20261119-01`
- وضعیت: `IN_PROGRESS`
- شاخهٔ کاری: `feat/multimarket-batch-data-pipeline`
- آخرین commit بررسی‌شده: `72a63a45de834151205579daf76af3f111073949`
- PR: [#1](https://github.com/yarsalam/marketsage/pull/1) — Draft، باز، ادغام‌نشده.
- مجوز مالک: اجرای خط لولهٔ خودکار برای تمام بازارهای مانیفست؛ دریافت داده، تشخیص وضعیت تعدیل، تعدیل مشروط، اعتبارسنجی و گزارش شکست‌های موردی.
- روش دستی و ماه‌به‌ماه/نمادبه‌نماد کنار گذاشته شد.
- داده‌ها و خروجی‌های قدیمی فاقد منشأ/هش معتبر از ورودی این کار کنار گذاشته می‌شوند؛ حذف یا بازنویسی نمی‌شوند.
- فایل پیوست `Financial.csv` نیز بنا بر دستور مالک از ورودی این کار کنار گذاشته شد.
- دریافت کامل تاریخچهٔ بازار و تعدیل سری واقعی هنوز اجرا نشده است.

## اسناد و کد ثبت‌شده
- `docs/DATA_SOURCE_CANDIDATES.md`: ماتریس اولیهٔ منابع و قواعد تعدیل هر کلاس.
- `docs/BATCH_PIPELINE_DESIGN.md`: معماری batch و state machine.
- `docs/SOURCE_PROBE_RESULTS.md`: نتایج نخستین probe کم‌حجم هفت endpoint.
- `config/source_registry.json`: رجیستری candidateها، endpointها، شواهد probe و وضعیت مجوز.
- `src/marketsage_pipeline/engine.py`: هستهٔ orchestrator، cache مبتنی بر request fingerprint، raw content-addressed و پردازش مستقل دارایی.
- `scripts/probe_sources.py`: probe فقط‌خواندنی و کم‌حجم.
- `tests/test_pipeline_engine.py`: هشت آزمون synthetic.
- `.github/workflows/pipeline-core-tests.yml` و `.github/workflows/source-probes.yml`: CI و probe منابع.

## شواهد آزمون و probe
- آزمون هسته: run `44555227688`، نتیجهٔ success؛ ۸ آزمون از ۸ آزمون synthetic موفق.
- probe اصلی منابع: run `44555538334`، نتیجهٔ success؛ artifact `14545386411`.
- محیط probe: GitHub-hosted Ubuntu 26.04 در westus3.
- TSETMC search: HTTP 200، پاسخ JSON معتبر و ۴۱ نتیجه برای «فولاد».
- TGJU history: HTTP 200؛ پاسخ بزرگ‌تر از سقف ۲۵۶ KiB probe؛ نیازمند pagination با start/length.
- NerkhAra index: HTTP 200؛ JSON معتبر ۱۴٬۳۶۶ بایتی و شامل metadata، ids و terms.
- NetArz currencies: HTTP 401؛ برای ادامه به API key نیاز دارد.
- Nobitex market stats: HTTP 200؛ JSON معتبر ۳۵۹ بایتی.
- Wallex markets: HTTP 200؛ پاسخ بزرگ‌تر از سقف probe؛ parse کامل انجام نشد.
- Alpha Vantage daily: HTTP 200؛ JSON معتبر ۲۱٬۳۰۰ بایتی با سری روزانهٔ IBM.
- یک probe تکراری ناخواسته با run `44555979408` به‌دلیل trigger شدن workflow هنگام تغییر رجیستری اجرا شد؛ نتیجهٔ آن در تصمیم منبع استفاده نمی‌شود. trigger اصلاح شد تا فقط تغییر اسکریپت probe باعث اجرای مجدد شود.
- probe فقط اتصال و ساختار محدود را سنجید؛ دادهٔ کامل ذخیره نشد و هیچ منبعی صرفاً با HTTP 200 پذیرفته نشده است.
- مستندات فنی TSETMC هشدار می‌دهد تاریخچهٔ GetClosingPriceDailyList ممکن است برای بسیاری از ابزارها خالی باشد؛ fallback باید بررسی شود.
- کد wrapper FIPIRAN، base service و endpointهای NAV را مشخص می‌کند؛ اتصال مستقیم هنوز probe نشده است.

## وضعیت منابع
- TSETMC: `PROBED`؛ جست‌وجو موفق، تاریخچه و رویدادها باز.
- TGJU: `PROBED`؛ پاسخ بزرگ، pagination لازم، مجوز نامشخص.
- NerkhAra: `PROBED`؛ index موفق، شناسه‌ها/terms/تاریخچهٔ نمونه باید بررسی شود.
- NetArz: `PROBED`؛ 401 بدون کلید.
- Nobitex: `PROBED`؛ آمار بازار موفق، OHLC باز.
- Wallex: `PROBED`؛ فهرست بازار بزرگ، OHLC باز.
- Alpha Vantage: `PROBED`؛ daily با demo key موفق، adjusted history و محدودیت free tier باز.
- FIPIRAN و CODAL: هنوز probe نشده‌اند.
- FRED/ALFRED و Nasdaq Data Link: هنوز probe نشده‌اند و به کلید/پلن یا انتخاب dataset نیاز دارند.
- هیچ منبعی هنوز `ACCEPTED` نیست؛ دریافت انبوه تا بررسی پوشش، محدودیت و حق استفاده متوقف است.

## معیارهای پذیرش
- [x] ماتریس اولیهٔ منابع و طراحی معماری batch ثبت شد.
- [x] هستهٔ orchestrator و state machine اولیه پیاده‌سازی شد.
- [x] هشت آزمون synthetic هسته در GitHub Actions موفق شد.
- [x] رجیستری candidateها و probe کم‌حجم هفت endpoint ثبت شد.
- [ ] تاریخچهٔ واقعی و رویدادها برای هر کلاس دریافت و schema آن‌ها تأیید شود.
- [ ] مجوز/محدودیت و پوشش هر منبع بررسی و منابع مناسب ACCEPTED شوند.
- [ ] adapter واقعی و universe discovery برای همهٔ کلاس‌ها پیاده‌سازی شود.
- [ ] تشخیص تعدیل و روش مستقل هر کلاس با دادهٔ واقعی آزمون شود.
- [ ] اجرای واحد batch تمام دارایی‌های فعال را بدون مداخلهٔ دستی پردازش کند.
- [ ] شکست یک دارایی، سایر دارایی‌ها را متوقف نکند.
- [ ] raw immutable، خروجی‌ها versioned و اجراها idempotent باشند.
- [ ] گزارش پوشش، کیفیت و شکست‌ها همراه شواهد ثبت شود.

## محدودیت‌ها
- فایل خام حذف یا بازنویسی نمی‌شود.
- روش یکسان برای همهٔ کلاس‌ها و ضریب حدسی ممنوع است.
- دادهٔ قدیمی فاقد provenance معتبر، ورودی pipeline جدید نیست.
- تحلیل سرمایه‌گذاری، رتبه‌بندی، معامله و اتصال کارگزاری خارج از این کار است.

## اقدام بعدی مجاز
ساخت adapterهای واقعی و دریافت کنترل‌شدهٔ تاریخچهٔ محدود برای هر کلاس، بررسی schema و وضعیت تعدیل از روی دادهٔ دریافتی، سپس توسعهٔ دریافت کامل و تعدیل. ابتدا TSETMC، FIPIRAN، TGJU/NerkhAra، Nobitex/Wallex و Alpha Vantage بررسی می‌شوند؛ NetArz تا تأمین کلید غیرفعال می‌ماند.

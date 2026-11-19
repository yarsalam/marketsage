# طراحی خط لولهٔ خودکار دادهٔ چندبازاری

## هدف
یک فرمان واحد، تمام دارایی‌های فعال مانیفست را در یک اجرای batch پردازش می‌کند. هیچ کار دستی برای تعدیل تک‌تک نمادها لازم نیست. هر دارایی state مستقل دارد و شکست یک مورد، بقیهٔ batch را متوقف نمی‌کند.

## اصل معماری
Orchestrator + Source Adapters + Asset-Class Processors + Validators + Evidence Ledger

Universe Registry
  -> Batch Orchestrator -> Checkpoint / Retry Queue / Run Ledger
  -> Source Adapter -> Immutable Raw Store + SHA256
  -> Schema Detector -> Canonical Normalizer
  -> Adjustment Detector
       -> already adjusted
       -> adjustment needed -> Event Ingestion -> Class Processor
  -> Quality Gates
       -> accepted
       -> review_required
       -> failed
  -> Versioned Output / Review Queue / Failure Ledger

## اجزای اصلی

### 1. Universe Registry
هر ابزار asset_id پایدار دارد؛ symbol فقط alias است. فیلدهای حداقلی:
- asset_id, asset_class, instrument_type
- source_id, source_instrument_id, exchange/market
- symbol, aliases, base/quote currency, unit
- timezone, trading_calendar, frequency
- active_from, active_to, status

### 2. Source Adapter
هر منبع قرارداد یکسان دارد:
- discover_universe()
- fetch_history(asset, start, end)
- fetch_events(asset, start, end)
- parse_response(raw)
- source_health()

Adapter باید timeout، rate limit، retry محدود برای خطاهای گذرا، pagination و backoff داشته باشد. خطاهای 401/403/404/410 و پاسخ schema ناشناخته retry بی‌پایان نمی‌شوند.

### 3. Immutable Raw Store
هر پاسخ خام با مسیر content-addressed یا run-scoped ذخیره می‌شود:
- source_id, request fingerprint, retrieved_at
- request parameters (بدون secret)
- HTTP status, response headers منتخب
- bytes, sha256, schema version
- license/terms reference

فایل خام overwrite نمی‌شود. پاسخ یکسان با hash برابر دوباره دانلود نمی‌شود مگر دلیل صریح در ledger وجود داشته باشد.

### 4. Canonical Schema
حداقل ستون‌های سری:
- asset_id, timestamp, session_date
- open, high, low, close, volume, value
- currency, price_unit, volume_unit
- source_id, source_record_id
- adjustment_status, adjustment_type
- raw_hash, pipeline_version

فیلدهای غیرقابل‌اعمال null می‌مانند؛ از یک close، OHLC جعلی ساخته نمی‌شود.

### 5. Adjustment Detection
خروجی detector یک label به‌همراه evidence است:
- ADJUSTED_VENDOR_CONFIRMED
- UNADJUSTED_CONFIRMED
- MIXED_OR_PARTIAL_ADJUSTMENT
- UNKNOWN

Detector باید متادیتای رسمی منبع، مستندات API، ستون‌های تعدیل، event history و continuity checks را ترکیب کند. تشخیص از روی کاهش/افزایش قیمت به‌تنهایی مجاز نیست.

### 6. Event Master و پردازشگرهای مستقل
- Equities: dividends, rights/capital increase, split/reverse split, merger, symbol/ISIN changes.
- Funds: cash distributions, unit changes, subscription/redemption NAV, reinvestment semantics.
- Gold/coins: specification/weight/fineness, quote basis and source changes.
- FX: rate type, pair direction, unit and source regime changes.
- Crypto: ticker/pair changes, chain migration, token swap, redenomination.
- Global: corporate actions, index methodology/version, futures expiry and roll.

هر event شامل effective date، announcement date، source evidence، event type، parameters، confidence و unresolved flags است. هیچ factor بدون event evidence محاسبه نمی‌شود.

### 7. Quality Gates
- schema/type/range validation
- timestamp ordering, duplicate and gap detection
- OHLC invariants: low <= open/close <= high (با tolerance مستند)
- volume/value non-negative
- discontinuity detector در روز رویداد و روزهای عادی
- source-vs-independent-source reconciliation
- adjusted-vs-raw relation and factor consistency
- no look-ahead: رویداد فقط از effective date به عقب روی تاریخچه اعمال می‌شود
- output lineage and hash verification

### 8. خروجی‌ها
برای هر asset:
- raw immutable
- normalized unadjusted
- vendor-adjusted (اگر ارائه‌دهنده دارد، بدون جایگزینی raw)
- internally adjusted price series
- total-return series (در صورت تعریف و دادهٔ کافی)
- event ledger
- quality report
- failure/review record

وضعیت نهایی: ACQUIRED, SCHEMA_VALIDATED, ADJUSTMENT_NOT_REQUIRED, ADJUSTED_VERIFIED, REVIEW_REQUIRED, SOURCE_FAILED, VALIDATION_FAILED.

## اجرای batch
- یک manifest واحد، چند adapter و چند processor را فعال می‌کند.
- پردازش هر دارایی در isolation انجام می‌شود.
- concurrency محدود به سیاست هر منبع است.
- retry فقط برای خطاهای گذرا و با سقف مشخص؛ عدم تکرار 401/403/404/410 و schema mismatch.
- checkpoint و request fingerprint اجرای مجدد را idempotent می‌کنند.
- run summary شامل شمارش هر وضعیت، coverage، freshness، duration و failure reason است.
- امکان اجرای مجدد فقط روی failed/review یا داده‌های تازه وجود دارد.

## معیار پذیرش نسخهٔ اول
1. تست قرارداد برای تمام adapterها.
2. تست synthetic fixture برای تمام وضعیت‌های detector.
3. تست رویدادهای شرکتی، تقسیم/تجمیع، توزیع صندوق، تغییر واحد/نماد، token migration و futures roll.
4. تست partial failure: یک adapter خراب شود اما سایر assetها تکمیل شوند.
5. تست idempotency: اجرای دوباره با ورودی/hash ثابت، raw و خروجی تکراری نسازد.
6. تست immutable raw و lineage.
7. اجرای end-to-end آزمایشی با یک دارایی از هر کلاس؛ سپس گسترش batch.

## ترتیب پیاده‌سازی
1. قراردادها، registry و orchestrator.
2. adapterهای منبع و دریافت خام.
3. schema detection و normalization.
4. adjustment detection.
5. event master و processorهای asset class.
6. quality gates و خروجی‌ها.
7. CI و اجرای batch کنترل‌شده.

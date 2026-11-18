# HANDOFF_STATE — MarketSage Adjustment Project

**آخرین به‌روزرسانی:** 2026-11-18 (جلسه ۳)
**HEAD:** (پس از commit بعدی ثبت می‌شود)
**Branch:** research/iran-equity-event-notebook-2026-11-12
**PR:** #82 (Draft)

## 🎯 وضعیت فعلی هر ۳ نماد

| نماد | event-ledger | adjusted_close | Total Return | تطبیق رسمی | پذیرش |
|---|---|---|---|---|---|
| **فولاد** | ✅ ۲۳ رویداد | ✅ ۴۲۶۹ ردیف | ❌ | ❌ | 🟡 **PROVISIONAL_WITH_CRITICAL_GAP** |
| **پارسیان** | ❌ ساخته نشده | ✅ ۳۵۴۲ ردیف | ❌ | ❌ | 🟡 **PROVISIONAL_UNTESTED** |
| **وغدیر** | ✅ ۸ ردیف (کهنه) | ✅ ۵۳۸۶ ردیف | ❌ | ❌ | 🟡 **PROVISIONAL_UNTESTED** |

## 🚨 blockerهای بحرانی

### B1 — ۷ ShareChange فولاد بدون PriceAdjust
- ۲۰۲۰-۰۱-۱۲: +۶۰٫۷۷٪
- ۲۰۲۱-۰۵-۲۴: +۴۰٫۱۹٪
- ۲۰۲۲-۰۸-۰۹: +۸۰٫۸۹٪
- ۲۰۲۳-۰۳-۱۹: +۵۰٫۹۴٪
- ۲۰۲۴-۰۲-۲۷: +۳۵٫۰۰٪
- ۲۰۲۵-۰۳-۱۲: +۳۸٫۸۹٪
- ۲۰۲۶-۰۳-۳۰: +۲۹٫۰۰٪
**تأثیر:** adjusted 2007 باید ۱۵٫۳ برابر کوچک‌تر باشد (۳٫۰۸ نه ۴۷٫۲۰)
**اقدام:** بررسی pagination TSETMC، یا تطبیق با نمودار رسمی

### B2 — نوع تأمین هر افزایش سرمایه نامشخص
**اقدام:** CODAL 38805/59965 (وغدیر) + معادل فولاد/پارسیان

### B3 — تطبیق با نمودار رسمی انجام نشده
**اقدام:** ساخت `comparison_vs_official.csv` برای هر ۳ نماد

### B4 — Total Return محاسبه نشده
**اقدام:** فرمول TR = (P_t + dividends_t) / P_{t-1} - 1

### B5 — فایل‌های کهنه vaghdir
`ADJUSTMENT_REPORT.md` (۴۸ خط) و `event-ledger.csv` (۸ خط) هنوز نسخه قدیمی‌اند (MS-DATA-001، A/B/C بدون تفکیک)
**اقدام:** بازنویسی در commit بعدی

## 📁 فایل‌های کلیدی

| فایل | مسیر | وضعیت |
|---|---|---|
| استاندارد | `docs/research/ADJUSTMENT_RESEARCH_STANDARD.md` | ✅ ۶۶ خط |
| موتور | `scripts/research/build_adjusted_series.py` | ✅ syntax OK |
| GOVERNANCE | `docs/governance/RELEASE_GATES.json` | RG-03/RG-04 NOT_PASSED |
| شاهد | `docs/governance/EVIDENCE_LEDGER.json` | EV-VAGHDIR با PARTIAL |
| فولاد event-ledger | `data/.../foolad/event-ledger.csv` | ✅ ۲۳ رویداد |
| فولاد adjusted | `data/.../foolad/derived/adjusted_close.csv` | ✅ ۴۲۶۹ ردیف |
| فولاد manifest | `data/.../foolad/derived/manifest.json` | ✅ SHA256 |
| پارسیان adjusted | `data/.../parsian/derived/adjusted_close.csv` | ✅ ۳۵۴۲ ردیف |
| وغدیر adjusted | `data/.../vaghdir/derived/adjusted_close.csv` | ✅ ۵۳۸۶ ردیف |

## 🎯 گام بعدی (به ترتیب)

| # | کار | اولویت |
|---|---|---|
| ۱ | ساخت `HANDOFF_STATE.md` (این فایل) + commit | 🔴 الان |
| ۲ | ساخت `foolad/validation/SYMBOL_ADJUSTMENT_ACCEPTANCE.json` با blocker B1 | 🔴 الان |
| ۳ | ساخت `parsian/event-ledger.csv` (مثل فولاد) | 🟡 |
| ۴ | بازنویسی `vaghdir/ADJUSTMENT_REPORT.md` + `event-ledger.csv` | 🟡 |
| ۵ | بررسی pagination TSETMC (B1) | 🔴 حیاتی |
| ۶ | تطبیق با نمودار رسمی (B3) | 🟡 |
| ۷ | Total Return (B4) | 🟡 |

## 📋 قوانین مرجع

1. `ADJUSTMENT_RESEARCH_STANDARD.md` — پروتکل
2. `RELEASE_GATES.json` — RG-03/RG-04 pass نشده
3. `DECISION_POLICY` — D-2026-11-16-01: ۳ نماد، PR #82، بدون دانلود مجدد
4. ممنوع: PR جدید، merge بدون تأیید، استفاده در بک‌تست

## 🔄 نحوه به‌روزرسانی این فایل

هر جلسه:
1. `git pull` (اگر جای دیگر کار شده)
2. آپدیت جدول وضعیت
3. اضافه/حذف blockerها
4. commit با پیام `chore(handoff): update state after session N`

## 📊 تاریخچه جلسات

| جلسه | تاریخ | کار انجام‌شده |
|---|---|---|
| ۱ | 2026-11-17 | governance sync (پالا) |
| ۲ | 2026-11-18 | ۵ کشف vaghdir، EVIDENCE_LEDGER بازنویسی |
| ۳ (این) | 2026-11-18 | استاندارد + موتور + ۳ سری adjusted، کشف B1 |

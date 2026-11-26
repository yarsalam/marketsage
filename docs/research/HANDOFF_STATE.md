# HANDOFF_STATE — MarketSage Adjustment Project

**آخرین به‌روزرسانی:** 2026-11-19 (جلسه ۵ — B3 حل، ۵ از ۶ blocker)
**HEAD:** (پس از commit بعدی)
**Branch:** research/iran-equity-event-notebook-2026-11-12
**PR:** #82 (Draft)

## 🎯 وضعیت فعلی هر ۳ نماد

| نماد | events | adjusted | Total Return | تطبیق TSE Client | پذیرش |
|---|---|---|---|---|---|
| **فولاد** | ✅ ۳۰ | ✅ ۴۲۶۹ | ✅ CAGR 47.7% | ✅ median 0.41% | 🟢 **PROVISIONAL_VERIFIED** |
| **پارسیان** | ✅ ۲۳ | ✅ ۳۵۴۲ | ✅ | ❌ نیازمند TSE Client | 🟡 PROVISIONAL |
| **وغدیر** | ✅ ۲۴ | ✅ ۵۳۸۶ | ✅ | ❌ نیازمند TSE Client | 🟡 PROVISIONAL |

## ✅ blockerهای حل‌شده (۵ از ۶)

### B1 — ✅ (ac62649): موتور v2 (SC-only)
۷/۵/۱ رویداد ShareChange به‌عنوان factor رایگان اعمال شد.

### B4 — ✅ (dc62b12): Total Return
Foolad CAGR 47.7%/19y. روش: `adj_close_t / adj_close_0 - 1`.

### B5 — ✅ (05bd419): vaghdir بازنویسی
گزارش + ledger هم‌گام.

### B6 — ✅ (840a2d1): `final_price` اولویت
`raw_close` = TSETMC `pClosing` (verified: 1900/3976/5270).

### B3 — ✅ (این جلسه): تطبیق با TSE Client 2.27.6 adjustInfo
- **median error: 0.41%** (truncation floor — TSE Client به عدد صحیح truncate می‌کند)
- **max 14.33%** فقط در قیمت‌های < 10 ریال (truncation)
- **TSE Client تأیید کرد که ۷ SC event را هم اعمال می‌کند** → فرض «رایگان» معتبر
- فایل: `validation/tse_client_adjustinfo.csv`

## 🔴 blocker باقی‌مانده (۱ از ۶)

### B2 — تأیید CODAL نوع تأمین افزایش سرمایه
- مسدود: CODAL HTTP 429
- **اثر:** برای `ACCEPTED` نهایی (نه PROVISIONAL) لازم است
- **گام:** منتظر رفع rate limit یا استفاده از `codal-mcp`

## 📁 فایل‌های کلیدی

| فایل | وضعیت |
|---|---|
| `docs/research/ADJUSTMENT_RESEARCH_STANDARD.md` | ✅ |
| `docs/research/HANDOFF_STATE.md` | ✅ این فایل |
| `scripts/research/build_adjusted_series.py` | ✅ v2 + B6 fix |
| `scripts/research/build_total_return.py` | ✅ |
| `scripts/research/compare_tse_client.py` | ✅ **جدید** |
| `data/.../foolad/validation/tse_client_adjustinfo.csv` | ✅ **جدید** |
| `data/.../foolad/validation/SYMBOL_ADJUSTMENT_ACCEPTANCE.json` | ✅ **PROVISIONAL_VERIFIED** |

## 🎯 گام بعدی

| # | کار | اولویت |
|---|---|---|
| ۱ | گرفتن TSE Client adjustInfo برای پارسیان و وغدیر | 🔴 بالا |
| ۲ | اعمال همان compare_tse_client.py برای هر دو | 🔴 بالا |
| ۳ | B2 (CODAL) — بلندمدت | 🟢 کم |
| ۴ | اتصال به پنل (فاز ۵) | 🟡 بعد از تأیید ۳ نماد |

## 📋 قوانین مرجع

1. `ADJUSTMENT_RESEARCH_STANDARD.md` — پروتکل
2. `RELEASE_GATES.json` — RG-03/RG-04 NOT_PASSED
3. `D-2026-11-16-01`: ۳ نماد، PR #82، بدون دانلود مجدد
4. ممنوع: PR جدید، merge بدون تأیید، استفاده در بک‌تست

## 📊 تاریخچه جلسات

| جلسه | تاریخ | کار |
|---|---|---|
| ۱ | 2026-11-17 | governance sync (پالا) |
| ۲ | 2026-11-18 | ۵ کشف vaghdir |
| ۳ | 2026-11-18 | استاندارد + موتور v1+v2 + ۳ سری |
| ۴ | 2026-11-18/19 | B6 + B4 + B5 |
| ۵ (این) | 2026-11-19 | **B3 حل با TSE Client** |

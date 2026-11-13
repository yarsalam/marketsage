# MarketSage Research

این پوشه شامل تحقیقات، متادیتا و گزارش‌های audit مربوط به پروژه MarketSage است.

## ساختار

- `source_inventory/`: لیست منابع داده و وضعیت دسترسی آن‌ها
- `raw_metadata/`: متادیتای خام از منابع مختلف (مثل CODAL)
- `audit_reports/`: گزارش‌های audit و نتایج بررسی
- `event_cases/`: پرونده‌های رویداد برای هر نماد
- `csv_exports/`: خروجی‌های CSV قابل خواندن
- `unresolved_questions/`: پرسش‌های باز و blockerها

## وضعیت فعلی

- داده‌های TSETMC برای سه نماد فولاد، وغدیر و پارسیان در حال بررسی است.
- فایل متادیتای CODAL با نام `codal_metadata_index.json` در خروجی اجرای audit محلی موجود است؛ هنوز در مسیر `raw_metadata/codal_metadata_index.json` این مخزن ثبت نشده است.
- گزارش فشرده audit با نام `three_symbol_audit_results.zip` در خروجی اجرای audit محلی موجود است؛ هنوز در مسیر `audit_reports/three_symbol_audit_results.zip` این مخزن ثبت نشده است.
- پیش از انتقال هر فایل به مخزن، مجوز انتشار، حساسیت داده، اندازه فایل و صحت checksum باید بررسی شود.
- ثبت این مستندات به‌معنای تأیید داده‌ها یا پذیرش هیچ الگوریتم تعدیل نیست.

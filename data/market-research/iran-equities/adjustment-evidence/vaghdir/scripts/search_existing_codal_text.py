# scripts/tmp/search_existing_codal_text.py
from pathlib import Path
import re

base = Path("data/market-research/iran-equities/adjustment-evidence/vaghdir/codal")

# تاریخ‌های ۵ بازه مبهم
target_dates = ["1390", "1391", "1392", "1394", "1404"]  # سال‌های شمسی مرتبط
keywords = ["افزایش سرمایه", "سود نقدی", "تقسیم سود", "مجمع عمومی"]

for txt_file in base.rglob("*.txt"):
    content = txt_file.read_text(encoding="utf-8", errors="ignore")
    for date in target_dates:
        if date in content:
            for kw in keywords:
                if kw in content:
                    print(f"\n=== {txt_file.name} | {date} | {kw} ===")
                    # نمایش ۲۰۰ کاراکتر اطراف کلمه کلیدی
                    idx = content.find(kw)
                    print(content[max(0, idx-100):idx+200])

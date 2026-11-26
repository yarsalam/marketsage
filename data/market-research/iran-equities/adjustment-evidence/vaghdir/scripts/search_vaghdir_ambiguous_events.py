# scripts/tmp/search_vaghdir_ambiguous_events.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ۴ بازه مبهم (تاریخ شمسی تقریبی)
TARGET_PERIODS = [
    {"label": "2010-04-21 (1389)", "from": "1389/01/15", "to": "1389/02/15"},
    {"label": "2011-04-26 (1390)", "from": "1390/01/15", "to": "1390/02/15"},
    {"label": "2013-02-27 (1391)", "from": "1391/11/15", "to": "1391/12/15"},
    {"label": "2015-03-17 (1393)", "from": "1393/12/15", "to": "1394/01/15"},
]

async def main():
    server_params = StdioServerParameters(command="uvx", args=["codal-mcp"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            for period in TARGET_PERIODS:
                print(f"\n{'='*60}")
                print(f"بازه: {period['label']}")
                print(f"از {period['from']} تا {period['to']}")
                print('='*60)

                # ۱. جستجوی آگهی ثبت افزایش سرمایه (id=28)
                print("\n--- آگهی ثبت افزایش سرمایه (id=28) ---")
                result = await session.call_tool(
                    "cd_search_letters",
                    arguments={
                        "symbol": "وغدیر",
                        "category": 7,
                        "letter_type": 28,
                        "from_date": period["from"],
                        "to_date": period["to"],
                    }
                )
                print(result)

                # ۲. جستجوی برنامه زمان‌بندی سود نقدی (id=30)
                print("\n--- برنامه زمان‌بندی سود نقدی (id=30) ---")
                result2 = await session.call_tool(
                    "cd_search_letters",
                    arguments={
                        "symbol": "وغدیر",
                        "letter_type": 30,  # این شناسه در گروه ۶ (مجامع) است
                        "from_date": period["from"],
                        "to_date": period["to"],
                    }
                )
                print(result2)

                # مکث بین درخواست‌ها (کدال محدودیت شدید دارد)
                await asyncio.sleep(5)

asyncio.run(main())

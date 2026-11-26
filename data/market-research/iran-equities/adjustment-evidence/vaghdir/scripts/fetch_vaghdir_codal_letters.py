import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def main():
    server_params = StdioServerParameters(
        command="uvx",
        args=["codal-mcp"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # جستجوی اطلاعیه‌های افزایش سرمایه وغدیر (گروه ۷ = افزایش سرمایه)
            result = await session.call_tool(
                "cd_search_letters",
                arguments={
                    "symbol": "وغدیر",
                    "letter_type": 7,  # افزایش سرمایه
                }
            )
            print("=== افزایش سرمایه ===")
            print(result)

            # جستجوی اطلاعیه‌های مجامع (برای سود نقدی)
            result2 = await session.call_tool(
                "cd_search_letters",
                arguments={
                    "symbol": "وغدیر",
                    "letter_type": 6,  # صورت‌های مالی / مجامع
                }
            )
            print("\n=== مجامع / سود نقدی ===")
            print(result2)

asyncio.run(main())

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(command="uvx", args=["codal-mcp"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # دریافت انواع اطلاعیه در گروه ۷ (افزایش سرمایه)
            result = await session.call_tool(
                "cd_letter_types",
                arguments={"category": 7}
            )
            print(result)

asyncio.run(main())

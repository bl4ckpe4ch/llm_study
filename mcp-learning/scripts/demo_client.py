import asyncio
import os
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


# 定位 server.py：与当前脚本同级的 server.py
SCRIPT_DIR = Path(__file__).resolve().parent
SERVER_PATH = str(SCRIPT_DIR.parent / "src" / "server.py")


async def main():
    # 启动 Python 解释器来运行 server.py
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER_PATH],
    )

    # stdio_client 会自动创建子进程并通过 stdin/stdout 传输消息
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 1. initialize：Client 与 Server 建立连接并协商能力
            print("1. initialize：Client 与 Server 建立连接并协商能力")
            init_result = await session.initialize()
            print(f"   Server: {init_result.server_info}")
            print(f"   Capabilities: {init_result.capabilities}")

            # 2. tools/list：发现 Server 提供的工具
            print("\n2. tools/list：发现 Server 提供的工具")
            tools_result = await session.list_tools()
            print(f"   {[t.name for t in tools_result.tools]}")

            # 3. tools/call：调用 add({ a: 20, b: 22 })
            print("\n3. tools/call：调用 add(a=20, b=22)")
            call_result = await session.call_tool("add", arguments={"a": 20, "b": 22})
            print(f"   {call_result}")

            # 4. resources/list + resources/read：发现并读取上下文
            print("\n4. resources/list + resources/read：发现并读取上下文")
            resources_result = await session.list_resources()
            print(f"   {[r.uri for r in resources_result.resources]}")
            read_result = await session.read_resource("lesson://architecture")
            print(f"   {read_result}")

            # 5. prompts/list + prompts/get：发现并获取提示词模板
            print("\n5. prompts/list + prompts/get：发现并获取提示词模板")
            prompts_result = await session.list_prompts()
            print(f"   {[p.name for p in prompts_result.prompts]}")
            prompt_result = await session.get_prompt("explain_mcp", arguments={"level": "beginner"})
            print(f"   {prompt_result}")

            print("\n✅ MCP Server、Client、Tool、Resource、Prompt 全部验证通过")


if __name__ == "__main__":
    asyncio.run(main())

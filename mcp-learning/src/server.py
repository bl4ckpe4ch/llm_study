import sys

from mcp.server.mcpserver import MCPServer


server = MCPServer("mcp-learning-demo", version="1.0.0")


# Tool: 让模型执行一个有明确输入和输出的动作。
@server.tool(title="两数相加", description="计算两个数字之和。用来学习 MCP Tool 的参数校验与返回值。")
def add(a: int, b: int) -> str:
    """计算两个数字之和。"""
    total = a + b
    return f"{a} + {b} = {total}"


# 学习卡片数据。
lessons: dict[str, str] = {
    "architecture": "MCP 采用 Host → Client → Server 架构。Host 是 Codex 等 AI 应用；Client 负责维护连接；Server 暴露工具、资源和提示词。",
    "transport": "本 demo 使用 stdio transport。Client 启动 Server 子进程，并通过 stdin/stdout 传输 JSON-RPC 消息。",
    "primitives": "Tool 是可执行动作；Resource 是可读取上下文；Prompt 是可复用的提示词模板。",
}


# Resource: 给模型提供可读取的上下文数据。
# 循环注册静态资源，让 list_resources 能列出所有具体 lesson URI。
# （模板资源 lesson://{topic} 也可以直接通过 URI 读取，但不会出现在 list 中。）
for _topic, _content in lessons.items():
    def _make_getter(content=_content):
        def getter() -> str:
            return content
        return getter

    server.resource(
        f"lesson://{_topic}",
        title=f"MCP 学习卡片: {_topic}",
        description=_content,
        mime_type="text/plain",
    )(_make_getter())


# Prompt: 为模型提供可复用的消息模板。
@server.prompt(title="解释 MCP", description="根据学习者水平生成一条 MCP 教学提示词。")
def explain_mcp(level: str) -> list:
    """根据学习者水平生成 MCP 教学提示词。"""
    if level == "beginner":
        text = "请用生活类比解释 MCP，并分别举例说明 Tool、Resource、Prompt。"
    else:
        text = "请从 Host、Client、Server、transport 和 capability negotiation 解释 MCP。"

    return [
        {
            "role": "user",
            "content": {"type": "text", "text": text},
        }
    ]


if __name__ == "__main__":
    server.run(transport="stdio")
    # stdio 的 stdout 专用于协议消息；调试信息只能写 stderr。
    print("mcp-learning-demo 已通过 stdio 启动", file=sys.stderr)

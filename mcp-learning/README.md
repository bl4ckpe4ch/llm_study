# MCP 入门 Demo

这是一个可以实际运行的最小 MCP（Model Context Protocol）项目。它不调用大模型，也不需要 API Key；重点是观察 **MCP Client 如何发现并调用 MCP Server 暴露的能力**。

## 先建立直觉

把 MCP 想象成 AI 应用的 USB-C：

```text
你
│
▼
Host（Codex / ChatGPT 等 AI 应用）
│
│ 内部创建 MCP Client
│
▼
MCP Client  ←── JSON-RPC 消息 / stdio ──→  MCP Server（本项目）
                                           ├── Tool: add
                                           ├── Resource: lesson://{topic}
                                           └── Prompt: explain_mcp
```

- **Host**：面向用户的 AI 应用，决定何时使用 MCP。
- **Client**：Host 内负责连接某一个 Server 的协议客户端。
- **Server**：向 Client 声明并提供能力。
- **Transport**：消息如何传输。本项目使用本地 `stdio`。

## 三个核心能力

| 能力 | 谁发起使用 | 本项目示例 | 直觉 |
|---|---|---|---|
| Tool | 通常由模型选择调用 | `add({a, b})` | 做一件事 |
| Resource | Client/应用读取 | `lesson://architecture` | 读一份数据 |
| Prompt | 用户/应用选择 | `explain_mcp` | 取一份提示词模板 |

## 运行

要求：Python 3.10+。

```bash
pip install -r requirements.txt
python scripts/demo_client.py
```

`demo_client.py` 会启动一个真实 MCP Client。它再通过 `stdio` 启动 Server，依次执行：

1. `initialize`：交换版本与能力；
2. `tools/list`：发现 `add`；
3. `tools/call`：调用加法工具；
4. `resources/list` 和 `resources/read`：读取学习卡片；
5. `prompts/list` 和 `prompts/get`：获取提示词。

### 再拆到底层：直接看 JSON-RPC

`demo_client.py` 使用的是 MCP 官方 Client SDK。想理解 SDK 替你做了什么，可以运行：

```bash
python scripts/raw_jsonrpc_client.py
```

这个脚本不使用 MCP Client SDK，而是直接启动 Server 子进程，向它的 stdin 写入一行一个 JSON-RPC 消息：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-11-25",
    "capabilities": {},
    "clientInfo": {
      "name": "raw-jsonrpc-client",
      "version": "1.0.0"
    }
  }
}
```

Server 的 stdout 也返回 JSON-RPC。所谓 MCP SDK，主要就是帮你封装连接、拆包、能力协商、类型校验和错误处理；协议本身并没有魔法。

## 连接到 Codex

把本地 stdio Server 加入 Codex。以下命令会修改 Codex 的 MCP 配置，所以建议你理解后手动执行：

```bash
codex mcp add mcp-learning-demo -- \
  python3 /Users/licongcong.sec/Documents/trae_projects/study/mcp-learning/src/server.py
```

查看是否配置成功：

```bash
codex mcp list
codex mcp get mcp-learning-demo
```

随后新开一个 Codex 会话，尝试：

```text
请使用 add 工具计算 123 + 456。
请读取 lesson://architecture，然后用自己的话解释。
```

移除配置：

```bash
codex mcp remove mcp-learning-demo
```

Codex 也支持项目级 `.codex/config.toml`。本 demo 没有自动写入配置，避免改变你当前 Codex 会话的外部状态。

## 建议阅读顺序

1. [`src/server.py`](src/server.py)：看 Server 如何注册 Tool、Resource、Prompt。
2. [`scripts/demo_client.py`](scripts/demo_client.py)：看 Client 如何连接、发现、调用。
3. 运行 `python scripts/raw_jsonrpc_client.py`，对照脚本看底层 JSON-RPC。
4. 修改 `add`，添加一个 `multiply` 工具。
5. 故意给 `add` 传字符串，观察类型校验错误。
6. 再尝试 Streamable HTTP transport，理解本地进程与远程服务的区别。

## Python 版本与 TypeScript 版本的差异

| 特性 | TypeScript 原版 | Python 版 |
|---|---|---|
| 类库 | `@modelcontextprotocol/sdk` + `zod` | `mcp`（官方 Python SDK v2） |
| Server 入口 | `McpServer` + `StdioServerTransport` | `MCPServer` + `server.run(transport="stdio")` |
| Tool 注册 | `server.registerTool(name, schema, handler)` | `@server.tool()` 装饰器 + Python 类型注解 |
| Resource 模板 | `ResourceTemplate` + 手动 `list` 回调 | 带 `{topic}` 占位符的 URI 自动成为模板 |
| Prompt 注册 | `server.registerPrompt(name, schema, handler)` | `@server.prompt()` 装饰器 |
| 参数校验 | `zod` schema | Python 函数签名 + 类型注解 |
| 调试日志 | `console.error` | `print(..., file=sys.stderr)` |

## 最重要的细节

`stdio` 模式下，Server 的 **stdout 只能输出 MCP 协议消息**。普通日志必须写到 stderr，所以 Server 使用 `print(..., file=sys.stderr)` 而不是 `print()`。一条随意的 stdout 日志就可能破坏 Client 对协议消息的解析。

## 参考

- [OpenAI 官方：MCP 与 Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [Model Context Protocol 官方文档](https://modelcontextprotocol.io/)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)

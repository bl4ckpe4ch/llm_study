import json
import subprocess
import sys
from pathlib import Path


# 定位 server.py
SCRIPT_DIR = Path(__file__).resolve().parent
SERVER_PATH = str(SCRIPT_DIR.parent / "src" / "server.py")


# MCP 的 stdio transport 本质上就是：一行一个 JSON-RPC 消息。
def main():
    # 启动 server 子进程，stdin/stdout/stderr 都用管道
    proc = subprocess.Popen(
        [sys.executable, SERVER_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
    )

    # 后台线程转发 server 的 stderr 到我们的 stderr
    import threading

    def forward_stderr():
        for line in proc.stderr:
            print(f"[server stderr] {line}", end="", file=sys.stderr)

    threading.Thread(target=forward_stderr, daemon=True).start()

    # 消息发送与接收
    def send(message: dict):
        line = json.dumps(message) + "\n"
        print("→ Client 发送：")
        print(json.dumps(message, indent=2, ensure_ascii=False))
        assert proc.stdin is not None
        proc.stdin.write(line)
        proc.stdin.flush()

    def recv() -> dict:
        assert proc.stdout is not None
        line = proc.stdout.readline()
        return json.loads(line.strip())

    # --- 协议对话 ---

    # 第一步：initialize
    send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {
                "name": "raw-jsonrpc-client",
                "version": "1.0.0",
            },
        },
    })

    msg = recv()
    print("← Server 返回：")
    print(json.dumps(msg, indent=2, ensure_ascii=False))

    if msg.get("error"):
        print(f"\n协议错误：{msg['error']['code']} {msg['error']['message']}", file=sys.stderr)
        proc.kill()
        sys.exit(1)

    # initialize 成功后，Client 需要补发一个 initialized 通知（无 id）
    send({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    })

    # 第二步：tools/list
    send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    })

    msg = recv()
    print("← Server 返回：")
    print(json.dumps(msg, indent=2, ensure_ascii=False))

    # 第三步：tools/call
    send({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "add",
            "arguments": {"a": 20, "b": 22},
        },
    })

    msg = recv()
    print("← Server 返回：")
    print(json.dumps(msg, indent=2, ensure_ascii=False))

    print("\n✅ 你刚刚没有使用 MCP Client SDK，而是直接说了一遍 MCP 协议。")

    proc.kill()


if __name__ == "__main__":
    main()

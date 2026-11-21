# MCP Server 配置示例

`vipeak-mcp` 是一个 Model Context Protocol server，让 Claude / Cursor / Codex 等 AI 客户端直接调用 Vipeak AI（123vips.com）的视频生成 API。

## 环境变量

| 变量 | 说明 |
|---|---|
| `VIPEAK_BASE_URL` | API 网关地址（登录 123vips.com 后 API Access 页面发放） |
| `VIPEAK_API_KEY` | Bearer token（同上） |

## Claude Desktop 配置

在 Claude Desktop 的配置文件中加入：

```json
{
  "mcpServers": {
    "vipeak": {
      "command": "python",
      "args": ["-m", "vipeak_mcp"],
      "env": {
        "VIPEAK_BASE_URL": "https://your-api-gateway",
        "VIPEAK_API_KEY": "your-key"
      }
    }
  }
}
```

## 手动测试（stdio）

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python -m vipeak_mcp
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python -m vipeak_mcp
```

## 提供的工具

- `estimate_credits` — 提交前估算积分成本
- `text_to_video` — 文生视频（异步）
- `image_to_video` — 图生视频（异步）
- `get_task` — 查询任务状态与结果
- `wait_for_video` — 创建并阻塞等待完成，返回结果 URL

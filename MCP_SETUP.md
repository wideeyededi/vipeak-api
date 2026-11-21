# MCP Server 配置示例

`vipeak-mcp` 是一个 Model Context Protocol server，让 Claude / Cursor / Codex 等 AI 客户端直接调用 Vipeak AI（123vip.fans / 123vips.com）的视频生成 API。

## 环境变量

| 变量 | 说明 |
|---|---|
| `VIPEAK_API_KEY` | Bearer token（API Access 包发放，必填） |
| `VIPEAK_BASE_URL` | API 网关地址（可选，默认 `https://123vip.fans`） |

## Claude Desktop 配置

```json
{
  "mcpServers": {
    "vipeak": {
      "command": "python",
      "args": ["-m", "vipeak_mcp"],
      "env": {
        "VIPEAK_BASE_URL": "https://123vip.fans",
        "VIPEAK_API_KEY": "sk-..."
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

- `list_models` — 查询模型目录（只读）
- `text_to_video` — 文生视频（异步，provider=seedance-nsfw / seedance25 / wan30 / *-vega）
- `image_to_video` — 图生视频（异步，带 referenceImages）
- `get_task` — 查询生成记录（GET /api/generation-records/<taskId>）
- `wait_for_video` — 创建并阻塞等待完成，返回结果
- `create_image` — 图片生成（seedream-5.0-pro / qwen-image-3.0）

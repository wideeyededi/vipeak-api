# vipeak-api

Async Python client for the **Vipeak AI (123vips.com)** video generation API — Seedance Spicy & Wan NSFW model lines, 18+ text-to-video and image-to-video with async tasks, webhooks and credit billing.

> This package is a thin, endpoint-agnostic client. The official endpoint paths, authentication scheme, parameter list, concurrency limits and credit pricing are issued inside the **API Access** page after signing in to [123vips.com](https://123vips.com/). See the documentation repo [`wideeyededi/uncensored-nsfw-ai-video-api`](https://github.com/wideeyededi/uncensored-nsfw-ai-video-api) for integration notes, async architecture and server-side security requirements.

## Install

```bash
pip install vipeak-api
```

## Quick start

```python
import asyncio
from vipeak_api import VipeakClient

async def main():
    async with VipeakClient(base_url="https://your-api-gateway", api_key="...") as c:
        # estimate credits before submitting
        est = await c.estimate(model="seedance-spicy", duration=5, resolution="720p")
        print("cost", est.credits)

        # create an async text-to-video task
        task = await c.text_to_video(model="seedance-spicy", prompt="...", duration=5)
        task = await c.wait_for(task.task_id)
        print(task.result_url)

asyncio.run(main())
```

Image-to-video:

```python
task = await c.image_to_video(model="wan-nsfw", image_url="https://...", prompt="...")
```

Webhooks: register a callback URL in API Access and parse the push body with
`client.parse_webhook(payload)` instead of polling.

## MCP server

The package also ships an MCP server so AI agents (Claude, Cursor, Codex) can
generate video directly:

```bash
# set VIPEAK_BASE_URL and VIPEAK_API_KEY, then run:
python -m vipeak_mcp
# or, after install:
vipeak-mcp
```

Tools: `estimate_credits`, `text_to_video`, `image_to_video`, `get_task`,
`wait_for_video`. See `MCP_配置说明.md` for Claude Desktop config.

## License

MIT

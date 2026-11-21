# vipeak-api

Async Python client for the **Vipeak AI** video generation API (123vip.fans / 123vips.com) — Seedance Spicy, Wan NSFW, and Vega model lines. 18+ text-to-video and image-to-video with async tasks, generation-record polling, and credit billing (1 USD = 100 credits).

> Official docs: https://123vip.fans/docs/api.md · Documentation repo: [`wideeyededi/uncensored-nsfw-ai-video-api`](https://github.com/wideeyededi/uncensored-nsfw-ai-video-api)

## Install

```bash
pip install vipeak-api
```

## Quick start

```python
import asyncio
from vipeak_api import VipeakClient

async def main():
    async with VipeakClient(api_key="sk-...") as c:
        # list available models (read-only)
        models = await c.list_models()

        # create an async text-to-video task (Seedance NSFW)
        resp = await c.advanced_generate(
            provider="seedance-nsfw",
            prompt="Use Image 1 as the subject reference.",
            ratio="9:16",
            resolution="720p",
            duration=8,
            generateAudio=True,
        )
        task_id = resp["taskId"]

        # poll until finished
        rec = await c.wait_for(task_id)
        print(rec)

asyncio.run(main())
```

### Providers

| Provider | Models | Capability |
| --- | --- | --- |
| `seedance-nsfw` | Seedance 2.5 NSFW | reference / first_last_frame / edit / extend |
| `seedance25` | Seedance 2.5 | reference / first_last_frame |
| `wan30` | W3.0 / Pro / Prime / VSR-Prime | `videoCapability`: `w3.0-video`, `w3.0-video-pro`, `w3.0-video-prime`, `w3.0-video-prime-pro` |
| `seedance25-vega` | Vega 1.5 Pro | text / frames / references / edit / extend / draft |
| `h3-vega` | Vega 1.5 Lite | text / frames / references |
| `seedance20-vega` | Vega 1.0 Pro | text / frames / references |
| `vega10-lite` | Vega 1.0 Lite | text / frames / references |

Image models: `seedream-5.0-pro`, `qwen-image-3.0-pro` / `qwen-image-3.0` (via `/api/v3/images/generations`), `z-image-spicy-pro` and `qwen-image-edit-spicy` (via `/api/wan27/image-edit`).

### Client methods

- `list_models()` — model catalog
- `upload_asset(**fields)` — reusable media upload
- `advanced_generate(**params)` — advanced video task
- `get_generation_record(task_id)` — poll advanced task
- `v3_create_task(payload)` / `v3_get_task(task_id)` — BytePlus-style V3 tasks
- `create_image(payload)` / `image_edit(payload)` — image generation
- `text_to_video(provider=..., prompt=..., ...)` — high-level helper
- `wait_for(task_id, ...)` — poll until terminal status

## MCP server

The package also ships an MCP server so AI agents (Claude, Cursor, Codex) can
generate video directly:

```bash
# set VIPEAK_API_KEY, then run:
python -m vipeak_mcp
# or, after install:
vipeak-mcp
```

Tools: `list_models`, `text_to_video`, `image_to_video`, `get_task`,
`wait_for_video`, `create_image`. See `MCP_SETUP.md` for Claude Desktop config.

## License

MIT

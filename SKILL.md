---
name: vipeak-api
description: Generate 18+ / uncensored AI videos and images through the Vipeak AI (123vip.fans) API — Seedance NSFW, Seedance 2.5, Wan 3.0 and Vega model lines. Text-to-video, image-to-video, reference-to-video, first/last-frame, edit and extend, with async task polling and credit billing. Use when the user asks to create adult or uncensored AI video/image content via Python or an MCP server.
---

# Vipeak AI — Uncensored AI Video Generation

Generate 18+ AI videos and images through the Vipeak AI (123vip.fans / 123vips.com) API using the official `vipeak-api` Python client and MCP server.

## What this does

- Text-to-video (T2V) and image-to-video (I2V) generation
- Reference-to-video, first/last-frame, video edit and extend
- Async task creation + generation-record polling
- Credit billing (1 USD = 100 credits)
- MCP server exposing video/image tools to Claude, Cursor and Codex

## Model lines

| Provider | Models |
| --- | --- |
| `seedance-nsfw` | Seedance 2.5 NSFW |
| `seedance25` | Seedance 2.5 |
| `wan30` | Wan 3.0 / Pro / Prime / VSR-Prime |
| `seedance25-vega` / `h3-vega` / `seedance20-vega` / `vega10-lite` | Vega 1.0/1.5 Pro & Lite |

Image models: `seedream-5.0-pro`, `qwen-image-3.0-pro`, `z-image-spicy-pro`, `qwen-image-edit-spicy`.

## Install

```bash
pip install vipeak-api
```

## Usage (Python)

```python
import asyncio
from vipeak_api import VipeakClient

async def main():
    async with VipeakClient(api_key="sk-...") as c:
        resp = await c.advanced_generate(
            provider="seedance-nsfw",
            prompt="Use Image 1 as the subject reference.",
            ratio="9:16", resolution="720p", duration=8, generateAudio=True,
        )
        rec = await c.wait_for(resp["taskId"])
        print(rec)

asyncio.run(main())
```

## Usage (MCP server)

```bash
# set VIPEAK_API_KEY, then run:
python -m vipeak_mcp
```

Exposed tools: `list_models`, `text_to_video`, `image_to_video`, `get_task`, `wait_for_video`, `create_image`.

## Important

- Requires a Vipeak AI API token (from the API Access package). Set it via `api_key=` (SDK) or `VIPEAK_API_KEY` (MCP); never hardcode it.
- Adults only. Enforce an 18+ gate and regional restrictions on your side.
- API docs: https://123vip.fans/docs/api.md

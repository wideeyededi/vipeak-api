"""Vipeak AI MCP server — expose Seedance / Wan / Vega video generation to AI agents.

A Model Context Protocol (MCP) server that lets Claude, Cursor, Codex and other
MCP clients generate 18+ text-to-video / image-to-video tasks through the
Vipeak AI API (123vip.fans / 123vips.com).

Wraps `vipeak_api.VipeakClient`. Credentials come from environment variables;
all tools map to the real endpoints documented at https://123vip.fans/docs/api.md.
"""

from __future__ import annotations

import json
import os

from vipeak_api import VipeakClient, DEFAULT_BASE_URL

__all__ = ["make_client", "TOOLS", "handle_call"]


def make_client() -> VipeakClient:
    """Build a client from environment variables.

    VIPEAK_BASE_URL — API base URL (optional, defaults to https://123vip.fans)
    VIPEAK_API_KEY  — Bearer token issued in the API Access package (required)
    """
    base = os.environ.get("VIPEAK_BASE_URL", DEFAULT_BASE_URL)
    key = os.environ.get("VIPEAK_API_KEY", "")
    if not key:
        raise RuntimeError(
            "VIPEAK_API_KEY must be set. Get it from the Vipeak AI API Access package."
        )
    return VipeakClient(base_url=base, api_key=key)


# JSON Schema for each tool, aligned with the real API fields.
TOOLS = [
    {
        "name": "list_models",
        "description": "Return the machine-readable model catalog (GET /api/models).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "text_to_video",
        "description": (
            "Create an async video task. Provide a provider (e.g. seedance-nsfw, "
            "seedance25, wan30, seedance25-vega, h3-vega, vega10-lite) plus prompt, "
            "ratio, resolution, duration and generateAudio. Returns the task id."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "provider id, e.g. seedance-nsfw or wan30"},
                "videoCapability": {"type": "string", "description": "optional Mulerouter node for wan30, e.g. w3.0-video-pro"},
                "prompt": {"type": "string"},
                "ratio": {"type": "string"},
                "resolution": {"type": "string"},
                "duration": {"type": "integer"},
                "generateAudio": {"type": "boolean"},
            },
            "required": ["provider", "prompt"],
        },
    },
    {
        "name": "image_to_video",
        "description": (
            "Create an async image-to-video task. Provide a provider and reference "
            "images (referenceImages: list of assetId / url objects), prompt, ratio, "
            "resolution and duration. Returns the task id."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string"},
                "prompt": {"type": "string"},
                "referenceImages": {"type": "array", "items": {"type": "object"}},
                "referenceVideos": {"type": "array", "items": {"type": "object"}},
                "ratio": {"type": "string"},
                "resolution": {"type": "string"},
                "duration": {"type": "integer"},
            },
            "required": ["provider"],
        },
    },
    {
        "name": "get_task",
        "description": "Poll an advanced task's generation record by task id (GET /api/generation-records/<taskId>).",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "wait_for_video",
        "description": "Create a video task and block until it finishes, then return the result URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string"},
                "prompt": {"type": "string"},
                "referenceImages": {"type": "array", "items": {"type": "object"}},
                "ratio": {"type": "string"},
                "resolution": {"type": "string"},
                "duration": {"type": "integer"},
                "timeout": {"type": "number", "description": "Max wait seconds (default 600)"},
            },
            "required": ["provider", "prompt"],
        },
    },
    {
        "name": "create_image",
        "description": "Create an image generation task (POST /api/v3/images/generations). model in {seedream-5.0-pro, qwen-image-3.0-pro, qwen-image-3.0}.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "prompt": {"type": "string"},
                "size": {"type": "string"},
                "n": {"type": "integer"},
            },
            "required": ["model", "prompt"],
        },
    },
]


async def handle_call(client: VipeakClient, name: str, args: dict) -> dict:
    """Dispatch an MCP tool call and return a JSON-serializable result."""
    if name == "list_models":
        return await client.list_models()

    if name == "text_to_video":
        payload = {"provider": args["provider"], "prompt": args["prompt"]}
        for k in ("videoCapability", "ratio", "resolution", "duration", "generateAudio"):
            if args.get(k) is not None:
                payload[k] = args[k]
        return await client.advanced_generate(**payload)

    if name == "image_to_video":
        payload = {"provider": args["provider"]}
        if args.get("prompt"):
            payload["prompt"] = args["prompt"]
        for k in ("referenceImages", "referenceVideos", "ratio", "resolution", "duration"):
            if args.get(k) is not None:
                payload[k] = args[k]
        return await client.advanced_generate(**payload)

    if name == "get_task":
        return await client.get_generation_record(args["task_id"])

    if name == "wait_for_video":
        payload = {"provider": args["provider"], "prompt": args["prompt"]}
        for k in ("referenceImages", "ratio", "resolution", "duration"):
            if args.get(k) is not None:
                payload[k] = args[k]
        resp = await client.advanced_generate(**payload)
        task_id = resp.get("taskId") or resp.get("id") or resp.get("task_id")
        if not task_id:
            return {"error": "no task id in create response", "response": resp}
        rec = await client.wait_for(task_id, timeout=args.get("timeout", 600.0))
        return rec

    if name == "create_image":
        payload = {"model": args["model"], "prompt": args["prompt"]}
        for k in ("size", "n"):
            if args.get(k) is not None:
                payload[k] = args[k]
        return await client.create_image(payload)

    raise ValueError(f"unknown tool: {name}")


async def serve_stdio():
    """Minimal stdio MCP server loop (JSON-RPC 2.0)."""
    import sys

    client = make_client()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method")
        rid = req.get("id")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": rid,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "vipeak-mcp", "version": "0.2.0"},
                },
            }
            print(json.dumps(resp), flush=True)

        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
            print(json.dumps(resp), flush=True)

        elif method == "tools/call":
            args = req.get("params", {}).get("arguments", {})
            name = req.get("params", {}).get("name", "")
            try:
                result = await handle_call(client, name, args)
                content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]
                resp = {"jsonrpc": "2.0", "id": rid, "result": {"content": content, "isError": False}}
            except Exception as e:  # noqa: BLE001
                content = [{"type": "text", "text": f"error: {e}"}]
                resp = {"jsonrpc": "2.0", "id": rid, "result": {"content": content, "isError": True}}
            print(json.dumps(resp, ensure_ascii=False), flush=True)

        elif method == "notifications/initialized":
            pass  # no response

    await client.aclose()


def main() -> None:
    import asyncio

    asyncio.run(serve_stdio())


if __name__ == "__main__":
    main()

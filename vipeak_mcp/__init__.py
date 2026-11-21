"""Vipeak AI MCP server — expose Seedance Spicy / Wan NSFW video generation to AI agents.

A minimal Model Context Protocol (MCP) server that lets Claude, Cursor, Codex
and other MCP clients generate 18+ text-to-video / image-to-video tasks through
the Vipeak AI (123vips.com) API.

The server wraps `vipeak_api.VipeakClient`. Base URL and credentials come from
environment variables; all tool endpoints mirror the official API Access docs.
"""

from __future__ import annotations

import json
import os

from vipeak_api import VipeakClient

__all__ = ["make_client", "TOOLS", "handle_call"]


def make_client() -> VipeakClient:
    """Build a client from environment variables.

    VIPEAK_BASE_URL — API base URL issued in the API Access page (required)
    VIPEAK_API_KEY  — Bearer token issued in the API Access page (required)
    """
    base = os.environ.get("VIPEAK_BASE_URL")
    key = os.environ.get("VIPEAK_API_KEY")
    if not base or not key:
        raise RuntimeError(
            "VIPEAK_BASE_URL and VIPEAK_API_KEY must be set. "
            "Get them from the API Access page after signing in to 123vips.com."
        )
    return VipeakClient(base_url=base, api_key=key)


# JSON Schema for each tool. Keep field names aligned with the official API.
TOOLS = [
    {
        "name": "estimate_credits",
        "description": "Estimate the credit cost of a video generation before submitting. Returns the credit amount so the user can confirm the price.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Model id, e.g. seedance-spicy or wan-nsfw"},
                "duration": {"type": "number", "description": "Clip duration in seconds"},
                "resolution": {"type": "string", "description": "e.g. 480p, 720p, 1080p"},
            },
            "required": ["model"],
        },
    },
    {
        "name": "text_to_video",
        "description": "Create an async text-to-video task. Returns a task id; poll or use a webhook to fetch the result.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Model id, e.g. seedance-spicy or wan-nsfw"},
                "prompt": {"type": "string", "description": "Text prompt describing the clip"},
                "duration": {"type": "number"},
                "resolution": {"type": "string"},
            },
            "required": ["model", "prompt"],
        },
    },
    {
        "name": "image_to_video",
        "description": "Create an async image-to-video task from a first-frame image URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "image_url": {"type": "string", "description": "URL of the first-frame image"},
                "prompt": {"type": "string"},
            },
            "required": ["model", "image_url"],
        },
    },
    {
        "name": "get_task",
        "description": "Fetch a task's status and result URL by task id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "wait_for_video",
        "description": "Create a task and block until it finishes (succeeds or fails), then return the result URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["text-to-video", "image-to-video"]},
                "model": {"type": "string"},
                "prompt": {"type": "string"},
                "image_url": {"type": "string"},
                "duration": {"type": "number"},
                "resolution": {"type": "string"},
                "timeout": {"type": "number", "description": "Max wait seconds (default 300)"},
            },
            "required": ["mode", "model"],
        },
    },
]


async def handle_call(client: VipeakClient, name: str, args: dict) -> dict:
    """Dispatch an MCP tool call and return a JSON-serializable result."""
    if name == "estimate_credits":
        est = await client.estimate(model=args["model"], **{k: v for k, v in args.items() if k != "model" and v is not None})
        return {"credits": est.credits}

    if name == "text_to_video":
        task = await client.text_to_video(
            model=args["model"],
            prompt=args["prompt"],
            resolution=args.get("resolution", "720p"),
            duration=args.get("duration", 5.0),
        )
        return {"task_id": task.task_id, "status": task.status}

    if name == "image_to_video":
        task = await client.image_to_video(
            model=args["model"],
            image_url=args["image_url"],
            prompt=args.get("prompt"),
        )
        return {"task_id": task.task_id, "status": task.status}

    if name == "get_task":
        task = await client.get_task(args["task_id"])
        return {
            "task_id": task.task_id,
            "status": task.status,
            "model": task.model,
            "result_url": task.result_url,
            "error": task.error,
        }

    if name == "wait_for_video":
        if args["mode"] == "text-to-video":
            task = await client.text_to_video(args["model"], args.get("prompt", ""), **{k: v for k, v in args.items() if k in ("resolution", "duration") and v is not None})
        else:
            task = await client.image_to_video(args["model"], args.get("image_url", ""), args.get("prompt"))
        task = await client.wait_for(task.task_id, timeout=args.get("timeout", 300.0))
        return {"task_id": task.task_id, "status": task.status, "result_url": task.result_url, "error": task.error}

    raise ValueError(f"unknown tool: {name}")


async def _stream_json(obj: dict):
    """Yield one JSON-RPC message line (for stdio transport)."""
    yield json.dumps(obj) + "\n"


async def serve_stdio():
    """Minimal stdio MCP server loop (JSON-RPC 2.0).

    Reads initialize/tools/list/tools/call requests from stdin and writes
    responses to stdout. This is the transport Claude Desktop and most MCP
    clients use.
    """
    import sys

    client = make_client()
    pending_result = None

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
                    "serverInfo": {"name": "vipeak-mcp", "version": "0.1.0"},
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

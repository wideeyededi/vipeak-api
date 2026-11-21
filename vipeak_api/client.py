"""Async client for the Vipeak AI (123vip.fans / 123vips.com) video generation API.

Wraps the real API surface documented at https://123vip.fans/docs/api.md:

- Advanced generation:  POST /api/advanced/generate -> taskId
                         GET  /api/generation-records/<taskId>
- V3 (BytePlus-style):   POST /api/v3/contents/generations/tasks
                         GET  /api/v3/contents/generations/tasks/<taskId>
- Image generation:      POST /api/v3/images/generations
- Image edit:            POST /api/wan27/image-edit
- Reusable media:        POST /api/user-assets
- Model catalog:         GET  /api/models

Billing: 1 USD = 100 credits. Advanced generation is charged per public rates.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

DEFAULT_BASE_URL = "https://123vip.fans"


class VipeakClient:
    """Async HTTP client for Vipeak AI video generation.

    Parameters
    ----------
    base_url:
        API base URL. Defaults to https://123vip.fans.
    api_key:
        Bearer token issued in the API Access package.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, api_key: str = "", timeout: float = 120.0) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "VipeakClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _post(self, path: str, payload: dict) -> dict:
        r = await self._client.post(f"{self._base}{path}", json=payload, headers=self._headers)
        r.raise_for_status()
        return r.json()

    async def _get(self, path: str) -> dict:
        r = await self._client.get(f"{self._base}{path}", headers=self._headers)
        r.raise_for_status()
        return r.json()

    # ---- catalog ----

    async def list_models(self) -> dict:
        """Return the machine-readable model catalog (GET /api/models)."""
        return await self._get("/api/models")

    # ---- reusable media ----

    async def upload_asset(self, **fields) -> dict:
        """Upload a reusable image/video/audio asset (POST /api/user-assets).

        Accepts url/imageUrl/videoUrl/audioUrl, dataUrl, name/fileName,
        durationSeconds, and provider. Returns the asset record including its id.
        """
        return await self._post("/api/user-assets", fields)

    # ---- advanced generation (Seedance / Wan / Vega) ----

    async def advanced_generate(self, **params) -> dict:
        """Create an advanced video task (POST /api/advanced/generate).

        Supply provider and videoCapability (or functionMode/mediaMode) plus
        prompt, references, ratio, resolution, duration, generateAudio, etc.
        Returns the raw create response, which carries the task id.
        """
        return await self._post("/api/advanced/generate", params)

    async def get_generation_record(self, task_id: str) -> dict:
        """Poll an advanced task's record (GET /api/generation-records/<taskId>)."""
        return await self._get(f"/api/generation-records/{task_id}")

    # ---- V3 (BytePlus-style) ----

    async def v3_create_task(self, payload: dict) -> dict:
        """Create a V3 task (POST /api/v3/contents/generations/tasks)."""
        return await self._post("/api/v3/contents/generations/tasks", payload)

    async def v3_get_task(self, task_id: str) -> dict:
        """Poll a V3 task (GET /api/v3/contents/generations/tasks/<taskId>)."""
        return await self._get(f"/api/v3/contents/generations/tasks/{task_id}")

    # ---- images ----

    async def create_image(self, payload: dict) -> dict:
        """Create an image task (POST /api/v3/images/generations)."""
        return await self._post("/api/v3/images/generations", payload)

    async def image_edit(self, payload: dict) -> dict:
        """Create an image-edit task (POST /api/wan27/image-edit)."""
        return await self._post("/api/wan27/image-edit", payload)

    # ---- high-level helpers ----

    async def text_to_video(
        self,
        provider: str = "seedance-nsfw",
        prompt: str = "",
        video_capability: Optional[str] = None,
        **params,
    ) -> dict:
        """Create a video task and return the raw create response (carries task id).

        For advanced providers (wan30 / seedance25 / seedance-nsfw / *-vega),
        pass `provider` and optional `videoCapability`; everything else is
        forwarded as request fields.
        """
        payload: dict[str, Any] = {"provider": provider}
        if video_capability:
            payload["videoCapability"] = video_capability
        if prompt:
            payload["prompt"] = prompt
        payload.update(params)
        return await self.advanced_generate(**payload)

    async def wait_for(
        self,
        task_id: str,
        poll_interval: float = 5.0,
        timeout: float = 600.0,
        poll_fn: str = "advanced",
    ) -> dict:
        """Poll until a task reaches a terminal status.

        poll_fn: "advanced" polls /api/generation-records/<id>, "v3" polls
        /api/v3/contents/generations/tasks/<id>.
        """
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            if poll_fn == "v3":
                rec = await self.v3_get_task(task_id)
            else:
                rec = await self.get_generation_record(task_id)
            status = rec.get("status", rec.get("data", {}).get("status", ""))
            if status in ("succeeded", "failed", "completed", "error"):
                return rec
            if loop.time() > deadline:
                raise TimeoutError(f"task {task_id} did not finish within {timeout}s")
            await asyncio.sleep(poll_interval)

    def parse_webhook(self, payload: dict) -> dict:
        """Parse a webhook callback body into a dict (data unwrapped)."""
        return payload.get("data", payload)

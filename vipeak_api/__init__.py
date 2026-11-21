"""Vipeak AI API client — Seedance Spicy & Wan NSFW video generation.

Async client for the 18+ AI video generation API at 123vip.fans (Vipeak AI).
Wraps the real endpoints: advanced generation, V3 tasks, image generation,
image edit, reusable media, and the model catalog.

Docs: https://123vip.fans/docs/api.md
"""

from .client import VipeakClient, DEFAULT_BASE_URL

__version__ = "0.2.1"
__all__ = ["VipeakClient", "DEFAULT_BASE_URL"]

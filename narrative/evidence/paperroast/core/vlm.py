#!/usr/bin/env python3
"""Thin OpenAI-compatible vision-chat client for local vLLM, OpenRouter and
Gemini. One function, no SDKs."""
from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path

import requests

KEYS_DIR = Path.home() / ".config" / "formidable"


def _key(name):
    p = KEYS_DIR / f"{name}.json"
    return json.loads(p.read_text())["api_key"] if p.exists() else None


PROVIDERS = {
    # architecture-controlled comparison: identical structured path, only the
    # model behind this table changes
    "local-2b":  {"endpoint": "http://localhost:8010/v1",
                  "model": "qwen3-vl-2b-v3", "key": None, "rep_pen": True},
    "local-8b":  {"endpoint": "http://localhost:8011/v1",
                  "model": "qwen3-vl-8b", "key": None, "rep_pen": True},
    "local-8b-tuned": {"endpoint": "http://localhost:8021/v1",
                       "model": "qwen3-vl-8b-v4", "key": None,
                       "rep_pen": True},
    "or-8b":     {"endpoint": "https://openrouter.ai/api/v1",
                  "model": "qwen/qwen3-vl-8b-instruct", "key": "openrouter"},
    "or-32b":    {"endpoint": "https://openrouter.ai/api/v1",
                  "model": "qwen/qwen3-vl-32b-instruct", "key": "openrouter"},
    "nanonets":  {"endpoint": "http://localhost:8012/v1",
                  "model": "nanonets-ocr2", "key": None},
    "gemini-flash": {"endpoint": "https://generativelanguage.googleapis.com/v1beta/openai",
                     "model": "gemini-2.5-flash", "key": "gemini",
                     "reasoning_effort": "none"},   # thinking eats max_tokens
}


def ask(image, prompt: str, provider: str | dict, max_tokens=256,
        temperature=0.0, timeout=240, retries=2) -> str:
    """image: PIL.Image. Returns the model's text reply."""
    cfg = PROVIDERS[provider] if isinstance(provider, str) else provider
    buf = io.BytesIO()
    image.save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    payload = {
        "model": cfg["model"], "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": prompt}]}],
    }
    if cfg.get("rep_pen"):
        payload["repetition_penalty"] = 1.05      # sibling: recall-neutral win
    if cfg.get("reasoning_effort"):
        payload["reasoning_effort"] = cfg["reasoning_effort"]
    headers = {"Content-Type": "application/json"}
    if cfg.get("key"):
        headers["Authorization"] = f"Bearer {_key(cfg['key'])}"
    url = cfg["endpoint"].rstrip("/") + "/chat/completions"
    last = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"] or ""
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"vlm call failed ({cfg['model']}): {last}")

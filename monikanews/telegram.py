# -*- coding: utf-8 -*-
"""Fetch recent messages from a Telegram channel for context."""

import httpx


def extract_text(message):
    """Extract readable text from a Telegram message dict."""
    if message.get("text"):
        return message["text"]
    if "photo" in message:
        return "[фото]"
    if "video" in message:
        return "[видео]"
    if "document" in message:
        return f"[документ: {message['document'].get('file_name', '')}]"
    return ""


async def fetch_channel_messages(bot_token, channel_id, limit=40):
    """Fetch the last `limit` text messages from a Telegram channel.
    Uses the Telegram Bot API getUpdates endpoint.
    Returns the most recent message texts (newest first).
    """
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {"limit": 100}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    result = data.get("result", [])
    channel_msgs = []
    for update in result:
        msg = update.get("message", {})
        if msg.get("chat", {}).get("id") == channel_id:
            text = extract_text(msg)
            if text:
                channel_msgs.append(text)
    return channel_msgs[-limit:][::-1]

# -*- coding: utf-8 -*-
import pytest
from monikanews.telegram import fetch_channel_messages, extract_text


def test_extract_text():
    assert extract_text({"text": "hello"}) == "hello"
    assert extract_text({"photo": [{}]}) == "[фото]"
    assert extract_text({"video": {}}) == "[видео]"
    assert extract_text({"document": {"file_name": "test.pdf"}}) == "[документ: test.pdf]"
    assert extract_text({}) == ""


@pytest.mark.asyncio
async def test_fetch_channel_messages(httpx_mock):
    mock_updates = {
        "result": [
            {"message": {"chat": {"id": -1001234567890}, "text": "Hello"}}
        ]
    }
    httpx_mock.add_response(json=mock_updates)
    msgs = await fetch_channel_messages("token", -1001234567890, limit=40)
    assert len(msgs) >= 1
    assert msgs[0] == "Hello"

# -*- coding: utf-8 -*-
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from monikanews.bot import (
    create_bot,
    handle_discussion_message,
    handle_news_command,
    process_chat_message,
)


ADMIN_CHAT_ID = 940454804
CHANNEL_ID = -1001234567890


def _plain_message(text="привет"):
    """MagicMock message that looks like an ordinary user text message."""
    m = MagicMock()
    m.text = text
    m.sender_chat = None
    m.is_automatic_forward = False
    m.answer = AsyncMock()
    return m


@pytest.mark.asyncio
async def test_create_bot_returns_dispatcher():
    with patch("monikanews.bot.Bot") as MockBot, patch("monikanews.bot.Dispatcher") as MockDispatcher:
        create_bot("test-token")
        MockBot.assert_called_once_with(token="test-token")
        MockDispatcher.assert_called_once()


@pytest.mark.asyncio
async def test_handle_news_command_filters_published():
    os.environ["CHANNEL_ID"] = str(CHANNEL_ID)
    import importlib
    import monikanews.bot
    importlib.reload(monikanews.bot)
    from monikanews.bot import handle_news_command
    mock_commit = {"message": "Remove httpx", "sha": "abc123def45678901234567890abcdef", "author": "FQingLars", "repo": "FQingLars/Monika-IT-bot", "date": "2026-09-20T15:00:00Z"}
    with patch("monikanews.bot.fetch_new_pushes") as MockFetch, patch("monikanews.bot.generate_news_article") as MockLLM, patch("monikanews.bot.fetch_channel_messages") as MockCtx, patch("monikanews.bot.save_commits_state"), patch("monikanews.bot.send_message") as MockSend:
        MockFetch.return_value = [mock_commit]
        MockCtx.return_value = ["old channel message"]
        with patch("monikanews.bot.load_commits_state") as MockLoadState:
            MockLoadState.return_value = {"last_timestamp": "2026-09-20T14:00:00Z", "FQingLars/Monika-IT-bot": {"abc123def45678901234567890abcdef": "published"}}
            message = MagicMock()
            message.chat.id = ADMIN_CHAT_ID
            message.answer = AsyncMock()
            await handle_news_command(message)
            MockLLM.assert_not_called()
            MockSend.assert_not_called()


@pytest.mark.asyncio
async def test_handle_news_command_sends_to_channel():
    os.environ["CHANNEL_ID"] = str(CHANNEL_ID)
    import importlib
    import monikanews.bot
    importlib.reload(monikanews.bot)
    from monikanews.bot import handle_news_command
    mock_commit = {"message": "Add new feature", "sha": "def456new789abcdef0123456789abcdef", "author": "FQingLars", "repo": "FQingLars/Monika-IT-bot", "date": "2026-09-20T16:00:00Z"}
    with patch("monikanews.bot.fetch_new_pushes") as MockFetch, patch("monikanews.bot.generate_news_article") as MockLLM, patch("monikanews.bot.fetch_channel_messages") as MockCtx, patch("monikanews.bot.save_commits_state"), patch("monikanews.bot.send_message") as MockSend, patch("monikanews.bot.save_last_commits"), patch("monikanews.bot.append_chat_message") as MockAppend:
        MockFetch.return_value = [mock_commit]
        MockCtx.return_value = ["old channel message"]
        MockLLM.return_value = "Here is the news!"
        with patch("monikanews.bot.load_commits_state") as MockLoadState:
            MockLoadState.return_value = {"last_timestamp": "2026-09-20T14:00:00Z"}
            message = MagicMock()
            message.chat.id = ADMIN_CHAT_ID
            message.answer = AsyncMock()
            await handle_news_command(message)
            MockLLM.assert_called_once()
            MockSend.assert_called_once()
            MockCtx.assert_called_once()
            MockAppend.assert_called_once_with("assistant", "Here is the news!")


@pytest.mark.asyncio
async def test_handle_news_command_non_admin():
    message = MagicMock()
    message.chat.id = 999999
    message.answer = AsyncMock()
    await handle_news_command(message)
    message.answer.assert_called_once_with("⚫ Доступ только для администратора.")


@pytest.mark.asyncio
async def test_handle_news_command_no_new_pushes():
    message = MagicMock()
    message.chat.id = ADMIN_CHAT_ID
    message.answer = AsyncMock()
    with patch("monikanews.bot.fetch_new_pushes") as MockFetch:
        MockFetch.return_value = []
        await handle_news_command(message)
    message.answer.assert_called_once_with("Пока нет данных о коммитах. Загляни чуть позже! (^_^)")


@pytest.mark.asyncio
async def test_process_chat_message_replies_and_saves_history():
    with patch("monikanews.bot.chat_reply", AsyncMock(return_value="Привет! Я Моника (^_^)")) as mock_chat, patch("monikanews.bot.load_chat_history", return_value=[]), patch("monikanews.bot.append_chat_message") as mock_append, patch("monikanews.bot.load_last_commits", return_value=[]):
        message = _plain_message("Привет")
        await process_chat_message(message)
        mock_chat.assert_awaited_once()
        message.answer.assert_awaited_once_with("Привет! Я Моника (^_^)")
        assert mock_append.call_count == 2


@pytest.mark.asyncio
async def test_process_chat_message_includes_recent_commits_context():
    commits = [{"sha": "abc123def456", "message": "fix", "repo": "FQingLars/X", "stats": {}, "files": []}]
    with patch("monikanews.bot.chat_reply", AsyncMock(return_value="ok")) as mock_chat, patch("monikanews.bot.load_chat_history", return_value=[]), patch("monikanews.bot.append_chat_message"), patch("monikanews.bot.load_last_commits", return_value=commits):
        message = _plain_message("Что нового?")
        await process_chat_message(message)
    kwargs = mock_chat.call_args.kwargs
    assert "abc123d" in kwargs["extra_context"]


@pytest.mark.asyncio
async def test_process_chat_message_ignores_channel_forwards():
    with patch("monikanews.bot.chat_reply", AsyncMock()) as mock_chat:
        message = MagicMock()
        message.sender_chat = MagicMock()  # channel post auto-forward
        message.is_automatic_forward = True
        message.answer = AsyncMock()
        await process_chat_message(message)
        mock_chat.assert_not_called()
        message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_handle_discussion_message_respects_cooldown():
    with patch("monikanews.bot.load_last_reply_ts", return_value=time.time()), patch("monikanews.bot.process_chat_message", AsyncMock()) as mock_proc, patch("monikanews.bot.save_last_reply_ts"):
        await handle_discussion_message(MagicMock())
        mock_proc.assert_not_called()


@pytest.mark.asyncio
async def test_handle_discussion_message_replies_after_cooldown():
    with patch("monikanews.bot.load_last_reply_ts", return_value=0.0), patch("monikanews.bot.process_chat_message", AsyncMock()) as mock_proc, patch("monikanews.bot.save_last_reply_ts") as mock_save:
        await handle_discussion_message(MagicMock())
        mock_proc.assert_awaited_once()
        mock_save.assert_called_once()

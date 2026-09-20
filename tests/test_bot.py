# -*- coding: utf-8 -*-
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from monikanews.bot import create_bot, handle_news_command


ADMIN_CHAT_ID = 940454804
CHANNEL_ID = -1001234567890


@pytest.mark.asyncio
async def test_create_bot_returns_dispatcher():
    bot_token = "test-token"
    with patch("monikanews.bot.Bot") as MockBot, patch("monikanews.bot.Dispatcher") as MockDispatcher:
        create_bot(bot_token)
        MockBot.assert_called_once_with(token=bot_token)
        MockDispatcher.assert_called_once()


@pytest.mark.asyncio
async def test_handle_news_command_filters_published():
    os.environ["CHANNEL_ID"] = str(CHANNEL_ID)
    import importlib
    import monikanews.bot
    importlib.reload(monikanews.bot)
    from monikanews.bot import handle_news_command
    mock_commit = {"message": "Remove httpx", "sha": "abc123def45678901234567890abcdef", "author": "FQingLars", "repo": "FQingLars/Monika-IT-bot", "date": "2026-09-20T15:00:00Z"}
    with patch("monikanews.bot.fetch_new_pushes") as MockFetch, patch("monikanews.bot.generate_news_article") as MockLLM, patch("monikanews.bot.fetch_channel_messages") as MockCtx, patch("monikanews.bot.save_commits_state") as MockSaveState, patch("monikanews.bot.send_message") as MockSend:
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
    with patch("monikanews.bot.fetch_new_pushes") as MockFetch, patch("monikanews.bot.generate_news_article") as MockLLM, patch("monikanews.bot.fetch_channel_messages") as MockCtx, patch("monikanews.bot.save_commits_state") as MockSaveState, patch("monikanews.bot.send_message") as MockSend:
        MockFetch.return_value = [mock_commit]
        MockCtx.return_value = ["old channel message"]
        with patch("monikanews.bot.load_commits_state") as MockLoadState:
            MockLoadState.return_value = {"last_timestamp": "2026-09-20T14:00:00Z"}
            MockLLM.return_value = "Here is the news!"
            message = MagicMock()
            message.chat.id = ADMIN_CHAT_ID
            message.answer = AsyncMock()
            await handle_news_command(message)
            MockLLM.assert_called_once()
            MockSaveState.assert_called_once()
            MockSend.assert_called_once()
            MockCtx.assert_called_once()


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
    message.answer.assert_called_once_with("📘 Нет данных о коммитах.")

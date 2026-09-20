# -*- coding: utf-8 -*-
"""Telegram bot that monitors GitHub pushes and posts LLM-generated news."""

import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command

from monikanews.github import fetch_new_pushes
from monikanews.llm import generate_news_article
from monikanews.state import (
    load_commits_state, save_commits_state,
    get_unpublished_commits, mark_published,
    get_last_timestamp, set_last_timestamp,
)
from monikanews.telegram import fetch_channel_messages


ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "940454804"))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1000000000000"))


router = Router()


@router.message(Command("news"))
async def handle_news_command(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        await message.answer("⚫ Доступ только для администратора.")
        return

    # Load commit states
    state_dict = load_commits_state()

    # Get last fetch timestamp for incremental fetch
    last_timestamp = get_last_timestamp(state_dict)

    # Fetch only NEW commits since last_timestamp
    commits = await fetch_new_pushes("FQingLars", last_timestamp)

    if not commits:
        await message.answer("📘 Нет данных о коммитах.")
        return

    # Filter to only unpublished commits
    new_commits = get_unpublished_commits(commits, state_dict)

    if not new_commits:
        await message.answer("📘 Ничего нового — все коммиты уже опубликованы.")
        return

    # Use only the most recent 3 unpublished commits
    commits = new_commits[:3]

    # Fetch channel messages as context (for LLM reference, not filtering)
    bot_token = os.environ.get("BOT_TOKEN", "")
    channel_context = await fetch_channel_messages(bot_token, CHANNEL_ID, limit=40)

    article = await generate_news_article(commits, context=channel_context)
    await send_message(CHANNEL_ID, article)

    # Mark commits as published
    for c in commits:
        mark_published(state_dict, c)

    # Update last_timestamp to the newest commit's date
    set_last_timestamp(state_dict, commits[0]["date"])

    # Save state
    save_commits_state(state_dict)

    await message.answer(f"✅ Новость опубликована в канале ({len(commits)} коммитов).")


async def send_message(chat_id: int, text: str):
    bot_token = os.environ.get("BOT_TOKEN", "")
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=text)
    await bot.session.close()


def create_bot(bot_token: str) -> Dispatcher:
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.bot = bot
    dp.include_router(router)
    return dp

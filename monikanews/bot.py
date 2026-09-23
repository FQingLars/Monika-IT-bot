# -*- coding: utf-8 -*-
"""Telegram bot: Monika persona, /news command and unified LLM chat."""

import os

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command

from monikanews.github import fetch_new_pushes
from monikanews.llm import chat_reply, format_commit, generate_news_article
from monikanews.state import (
    append_chat_message,
    get_last_timestamp,
    get_unpublished_commits,
    load_chat_history,
    load_commits_state,
    load_last_commits,
    mark_published,
    save_commits_state,
    save_last_commits,
    set_last_timestamp,
)
from monikanews.telegram import fetch_channel_messages


ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "940454804"))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1000000000000"))
COMMENTS_CHAT_ID = int(os.environ.get("COMMENTS_CHAT_ID", "0"))


router = Router()


def _recent_commits_context() -> str:
    """Short context block about recent commits for Monika's chat replies."""
    commits = load_last_commits()
    if not commits:
        return ""
    lines = [format_commit(c) for c in commits[:3]]
    return "Последние известные тебе коммиты:\n" + "\n".join(lines)


async def process_chat_message(message: types.Message) -> None:
    """Unified Monika chat: reply via LLM and remember the dialog."""
    text = message.text or ""
    history = load_chat_history()
    reply = await chat_reply(
        text,
        history=history,
        extra_context=_recent_commits_context() or None,
    )
    await message.answer(reply)
    append_chat_message("user", text)
    append_chat_message("assistant", reply)


@router.message(Command("news"))
async def handle_news_command(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        await message.answer("⚫ Доступ только для администратора.")
        return

    state_dict = load_commits_state()
    last_timestamp = get_last_timestamp(state_dict)
    commits = await fetch_new_pushes("FQingLars", last_timestamp)

    if not commits:
        await message.answer("Пока нет данных о коммитах. Загляни чуть позже! (^_^)")
        return

    save_last_commits(commits[:3])

    new_commits = get_unpublished_commits(commits, state_dict)
    if not new_commits:
        await message.answer("Новых коммитов пока нет. Но я слежу и сразу напишу, как что-то появится! (^_^)")
        return

    commits = new_commits[:3]

    bot_token = os.environ.get("BOT_TOKEN", "")
    channel_context = await fetch_channel_messages(bot_token, CHANNEL_ID, limit=40)

    article = await generate_news_article(commits, context=channel_context)
    await send_message(CHANNEL_ID, article)

    for c in commits:
        mark_published(state_dict, c)
    set_last_timestamp(state_dict, commits[0]["date"])
    save_commits_state(state_dict)

    await message.answer(f"✅ Новость опубликована в канале ({len(commits)} коммитов).")


@router.message(F.chat.type == "private", F.text, ~F.text.startswith("/"))
async def handle_private_message(message: types.Message):
    await process_chat_message(message)


@router.message(
    F.chat.id == COMMENTS_CHAT_ID,
    F.text,
    F.from_user.is_bot == False,  # noqa: E712
    ~F.text.startswith("/"),
)
async def handle_discussion_message(message: types.Message):
    await process_chat_message(message)


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

# -*- coding: utf-8 -*-
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from monikanews.llm import (
    PERSONA_PATH,
    chat_reply,
    format_commit,
    generate_news_article,
    load_persona,
)


def _mock_response(content="news"):
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content=content))]
    return resp


@pytest.mark.asyncio
async def test_persona_file_exists_and_loaded():
    assert PERSONA_PATH.exists()
    persona = load_persona()
    assert "Моника" in persona
    assert len(persona) > 100


@pytest.mark.asyncio
async def test_generate_news_article_system_persona():
    commits = [{"message": "fix bug", "sha": "abc123def456", "repo": "FQingLars/Monika-IT-bot"}]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=_mock_response())
        await generate_news_article(commits)
    messages = instance.chat.completions.create.call_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert "Моника" in messages[0]["content"]
    user = messages[1]["content"]
    assert "abc123d" in user
    assert "FQingLars/Monika-IT-bot" in user
    assert "3-5 предложений" in user


@pytest.mark.asyncio
async def test_generate_news_article_multi_repo_in_prompt():
    commits = [
        {"message": "book sync", "sha": "aaaa1111", "repo": "FQingLars/QLISP-Project"},
        {"message": "bot update", "sha": "bbbb2222", "repo": "FQingLars/Monika-IT-bot"},
    ]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=_mock_response())
        await generate_news_article(commits)
    user = instance.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "FQingLars/QLISP-Project" in user
    assert "FQingLars/Monika-IT-bot" in user


@pytest.mark.asyncio
async def test_generate_news_article_one_call_total():
    commits = [
        {"message": "fix bug", "sha": "abc123", "repo": "FQingLars/Monika-IT-bot"},
        {"message": "add feature", "sha": "def456", "repo": "FQingLars/Monika-IT-bot"},
    ]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=_mock_response())
        await generate_news_article(commits)
    assert instance.chat.completions.create.call_count == 1


@pytest.mark.asyncio
async def test_generate_news_article_stats_and_files_in_prompt():
    commits = [{
        "message": "fix bug",
        "sha": "abc123def456",
        "repo": "FQingLars/Monika-IT-bot",
        "stats": {"additions": 5, "deletions": 2, "total": 7},
        "files": ["monikanews/llm.py", "tests/test_llm.py"],
    }]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=_mock_response())
        await generate_news_article(commits)
    user = instance.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "+5 -2" in user
    assert "monikanews/llm.py" in user


@pytest.mark.asyncio
async def test_generate_news_article_no_new_commits():
    article = await generate_news_article([])
    assert "нет новых коммитов" in article


def test_format_commit():
    commit = {
        "sha": "abc123def456",
        "message": "fix bug",
        "repo": "FQingLars/QLISP-Project",
        "stats": {"additions": 5, "deletions": 2, "total": 7},
        "files": ["file1.py", "file2.py"],
    }
    result = format_commit(commit)
    assert "FQingLars/QLISP-Project" in result
    assert "+5 -2" in result
    assert "file1.py" in result


@pytest.mark.asyncio
async def test_chat_reply_builds_messages():
    history = [
        {"role": "user", "content": "привет"},
        {"role": "assistant", "content": "о, привет! (^_^)"},
    ]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=_mock_response("ответ"))
        reply = await chat_reply("как дела?", history=history, extra_context="Контекст коммитов")
    assert reply == "ответ"
    messages = instance.chat.completions.create.call_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert "Моника" in messages[0]["content"]
    assert messages[1] == {"role": "system", "content": "Контекст коммитов"}
    assert messages[2]["content"] == "привет"
    assert messages[3]["content"] == "о, привет! (^_^)"
    assert messages[-1] == {"role": "user", "content": "как дела?"}


@pytest.mark.asyncio
async def test_generate_news_article_uses_env_token():
    import os
    os.environ["OPENROUTER_TOKEN"] = "test-token-123"
    commits = [{"message": "hello", "sha": "abc123", "repo": "FQingLars/Monika-IT-bot"}]
    try:
        with patch("monikanews.llm.AsyncOpenAI") as MockClient:
            instance = MockClient.return_value
            instance.chat.completions.create = AsyncMock(return_value=_mock_response())
            await generate_news_article(commits)
        init_kwargs = MockClient.call_args.kwargs
        assert init_kwargs["api_key"] == "test-token-123"
        assert init_kwargs["base_url"] == "https://openrouter.ai/api/v1"
    finally:
        os.environ.pop("OPENROUTER_TOKEN", None)

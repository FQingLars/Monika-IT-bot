# -*- coding: utf-8 -*-
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from monikanews.llm import generate_news_article, _format_commit


@pytest.mark.asyncio
async def test_generate_news_article_returns_text():
    commits = [{"message": "fix", "sha": "abc123", "repo": "FQingLars/Monika-IT-bot"}]
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="news"))]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        article = await generate_news_article(commits)
    assert isinstance(article, str) and len(article) > 0


@pytest.mark.asyncio
async def test_generate_news_article_one_call_total():
    commits = [
        {"message": "fix bug", "sha": "abc123", "repo": "FQingLars/Monika-IT-bot"},
        {"message": "add feature", "sha": "def456", "repo": "FQingLars/Monika-IT-bot"},
    ]
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="news"))]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        await generate_news_article(commits)
    assert instance.chat.completions.create.call_count == 1


@pytest.mark.asyncio
async def test_generate_news_article_all_commits_in_prompt():
    commits = [
        {"message": "fix bug", "sha": "abc123def456", "repo": "FQingLars/Monika-IT-bot"},
        {"message": "add feature", "sha": "def456new789", "repo": "FQingLars/Monika-IT-bot"},
    ]
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="news"))]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        await generate_news_article(commits)
    call_content = instance.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "abc123d" in call_content
    assert "def456n" in call_content
    assert "Monika" in call_content
    assert "3-5 предложений" in call_content
    assert "PythonPortal" not in call_content


@pytest.mark.asyncio
async def test_generate_news_article_stats_and_files_in_prompt():
    commits = [
        {
            "message": "fix bug",
            "sha": "abc123def456",
            "repo": "FQingLars/Monika-IT-bot",
            "stats": {"additions": 5, "deletions": 2, "total": 7},
            "files": ["monikanews/llm.py", "tests/test_llm.py"],
        },
    ]
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="news"))]
    with patch("monikanews.llm.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        await generate_news_article(commits)
    call_content = instance.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "+5 -2" in call_content
    assert "monikanews/llm.py" in call_content


@pytest.mark.asyncio
async def test_format_commit():
    commit = {
        "sha": "abc123def456",
        "message": "fix bug",
        "stats": {"additions": 5, "deletions": 2, "total": 7},
        "files": ["file1.py", "file2.py", "file3.py"],
    }
    result = _format_commit(commit)
    assert "+5 -2" in result
    assert "file1.py" in result
    assert "file2.py" in result
    assert "file3.py" in result


@pytest.mark.asyncio
async def test_generate_news_article_uses_env_token():
    import os
    os.environ["OPENROUTER_TOKEN"] = "test-token-123"
    commits = [{"message": "hello", "sha": "abc123", "repo": "FQingLars/Monika-IT-bot"}]
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="news"))]
    try:
        with patch("monikanews.llm.AsyncOpenAI") as MockClient:
            instance = MockClient.return_value
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            await generate_news_article(commits)
        init_kwargs = MockClient.call_args.kwargs
        assert init_kwargs["api_key"] == "test-token-123"
        assert init_kwargs["base_url"] == "https://openrouter.ai/api/v1"
    finally:
        os.environ.pop("OPENROUTER_TOKEN", None)

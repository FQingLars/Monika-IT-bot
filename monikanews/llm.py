# -*- coding: utf-8 -*-
"""LLM client for generating Monika-style news articles."""

import os
from openai import AsyncOpenAI


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _make_hashtags(repo_name: str) -> str:
    parts = repo_name.replace("FQingLars/", "").replace("-", " ").split()
    tags = []
    for p in parts[:3]:
        tags.append("#" + p)
    if not tags:
        tags = ["#bot", "#github", "#news"]
    return " ".join(tags[:3])


def _make_hashtags_extra(repo_name: str) -> str:
    extra = ["#opensource", "#devlife", "#commit"]
    return " ".join(extra)


def _format_commit(commit: dict) -> str:
    """Format a commit with stats and files."""
    sha = commit.get("sha", "")[:7]
    msg = commit.get("message", "")
    stats = commit.get("stats", {})
    files = commit.get("files", [])
    additions = stats.get("additions", 0)
    deletions = stats.get("deletions", 0)
    files_str = ", ".join(files[:5]) if files else "нет изменений"
    if len(files) > 5:
        files_str += f" и {len(files) - 5} ещё"
    return f"- Коммит {sha}: {msg} (+{additions} -{deletions}, {files_str})"


async def generate_news_article(commits: list[dict], context: list[str] | None = None, model: str | None = None) -> str:
    if not commits:
        return "Ничего нового. Сидите и ждите.\n"
    if model is None:
        model = os.environ.get("MODEL", "publisher/model")
    openrouter_token = os.environ.get("OPENROUTER_TOKEN", "")

    client = AsyncOpenAI(api_key=openrouter_token, base_url=OPENROUTER_BASE_URL)

    ctx_str = ""
    if context:
        recent = [c for c in context if isinstance(c, str) and len(c) > 10][-5:]
        if recent:
            ctx_str = "\n\nНедавние сообщения в канале:\n" + "\n".join(f"- {c}" for c in recent)

    commits_detail = "\n".join(_format_commit(c) for c in commits)

    repo_name = commits[0].get("repo", "unknown")
    
    prompt = (
        "Monika следит за репозиторием " + repo_name + ". Вот последние коммиты:\n\n"
        + commits_detail +
        "\n\n"
        "Напиши НОВОСТЬ на русском языке на 3-5 предложений. "
        "Тон: элегантный, саркастичный, женщина с интеллектуальным самомнением "
        "которая читает коммиты и делает из них новость. "
        "Никаких шуток про Python, никаких шаблонных фраз. "
        "Используй только факты из коммитов — что именно было сделано. "
        "Будь убедительной, как будто ты давно следишь за этим проектом "
        "и тебе надоели эти коммиты но ты всё равно напишешь новость. "
        "Стиль: типичный редактор который знает что делает но терпеть не может "
        "свою работу. Никакого маркдауна, никаких заголовков в формате ###."
        + ctx_str +
        "\n\nНовая новость:"
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    article = response.choices[0].message.content.strip()
    
    tags = _make_hashtags(repo_name) + "\n" + _make_hashtags_extra(repo_name)
    return article + "\n\n" + tags

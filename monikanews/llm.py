# -*- coding: utf-8 -*-
"""LLM client: Monika persona from persona.md + news and chat generation."""

import os
from pathlib import Path

from openai import AsyncOpenAI


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PERSONA_PATH = Path(__file__).resolve().parent / "persona.md"


def load_persona() -> str:
    """Load the Monika persona system prompt."""
    try:
        return PERSONA_PATH.read_text(encoding="utf-8")
    except OSError:
        return (
            "Ты — Моника, тёплая и обаятельная ведущая MonikaNews. "
            "Говори по-русски на ты, только факты, без Markdown."
        )


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


def format_commit(commit: dict) -> str:
    """Format one commit: repo, sha, message, stats, files."""
    repo = commit.get("repo", "unknown")
    sha = commit.get("sha", "")[:7]
    msg = commit.get("message", "")
    stats = commit.get("stats", {})
    files = commit.get("files", [])
    additions = stats.get("additions", 0)
    deletions = stats.get("deletions", 0)
    files_str = ", ".join(files[:5]) if files else "нет изменений"
    if len(files) > 5:
        files_str += f" и ещё {len(files) - 5}"
    return f"- {repo} — коммит {sha}: {msg} (+{additions} -{deletions}, {files_str})"


async def _complete(messages: list[dict], model: str | None) -> str:
    if model is None:
        model = os.environ.get("MODEL", "publisher/model")
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_TOKEN", ""),
        base_url=OPENROUTER_BASE_URL,
    )
    response = await client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content.strip()


async def generate_news_article(
    commits: list[dict],
    context: list[str] | None = None,
    model: str | None = None,
) -> str:
    """Generate a Monika-style news post about the given commits."""
    if not commits:
        return "Пока нет новых коммитов. Напишу, как только что-то появится! (^_^)\n"

    ctx_str = ""
    if context:
        recent = [c for c in context if isinstance(c, str) and len(c) > 10][-5:]
        if recent:
            ctx_str = "\n\nНедавние сообщения в канале:\n" + "\n".join(f"- {c}" for c in recent)

    repo_name = commits[0].get("repo", "unknown")
    commits_detail = "\n".join(format_commit(c) for c in commits)
    task = (
        "Задача: напиши новость для канала о коммитах ниже. "
        "Объём 3-5 предложений, только факты из коммитов, без Markdown, без хэштегов. "
        "Внимание: коммиты могут быть из разных репозиториев — для каждого изменения "
        "указывай, из какого он репозитория.\n\n"
        "Коммиты:\n" + commits_detail + ctx_str + "\n\nНовость:"
    )
    messages = [
        {"role": "system", "content": load_persona()},
        {"role": "user", "content": task},
    ]
    article = await _complete(messages, model)
    tags = _make_hashtags(repo_name) + "\n" + _make_hashtags_extra(repo_name)
    return article + "\n\n" + tags


async def chat_reply(
    user_text: str,
    history: list[dict] | None = None,
    extra_context: str | None = None,
    model: str | None = None,
) -> str:
    """Reply to a chat message as Monika using the persona and dialog history."""
    messages = [{"role": "system", "content": load_persona()}]
    if extra_context:
        messages.append({"role": "system", "content": extra_context})
    for msg in history or []:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})
    return await _complete(messages, model)

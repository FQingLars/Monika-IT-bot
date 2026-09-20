# MonikaNews — Agents Rules

## Talk Before Coding
- Always ask clarifying questions before writing production code.
- Do not assume; confirm intent, scope, and constraints with the user first.

## TDD (Test-Driven Development)
- Write a failing test FIRST, then make it pass, then refactor.
- No production code without a corresponding test.
- Keep tests fast, isolated, and deterministic.

## KISS (Keep It Simple, Stupid)
- Prefer the simplest solution that works.
- Avoid over-engineering; add complexity only when justified.
- Favor readability and maintainability over cleverness.

## Project Conventions
- Never commit or read `.env` (contains secrets). Use `.env.example` as the template.
- Python 3.12 virtualenv is at `.venv/`; activate before running scripts.
- Source code lives at the project root unless a package layout is justified.
- Configuration keys (from .env.example): BOT_TOKEN, MODEL, OPENROUTER_TOKEN, CHANNEL_ID, COMMENTS_CHAT_ID, ADMIN_CHAT_ID.
- State directory (`state/`) is gitignored — persist runtime data there.
- Use `python-dotenv` to load .env; call `load_dotenv()` at module entry point.

## SDK Notes
- OpenAI SDK: `OpenAI` is sync, `AsyncOpenAI` is async. Use `AsyncOpenAI` inside async functions.
- aiogram 3.x: `Dispatcher` has no `.bot` by default — set `dp.bot = Bot(...)` in `create_bot()`. Use `await dp.start_polling(dp.bot)`.
- gh CLI: GitHub API uses `gh api /repos/FQingLars/Monika-IT-bot/commits?since=<ISO-8601>`. Async via `asyncio.create_subprocess_exec`.
- httpx: `resp.json()` is synchronous (no await). Used only for Telegram Bot API in telegram.py.

## Workflow
1. Understand the task.
2. Ask questions (Talk Before Coding).
3. Write tests (TDD).
4. Implement to pass tests (KISS).
5. Verify, iterate.

## Decisions (Talk Before Coding)
- GitHub user: FQingLars
- Repo: FQingLars/Monika-IT-bot (monitored repo, hardcoded in github.py)
- Trigger: Admin sends /news command in Telegram (chat_id 940454804)
- Detection: `gh api /repos/FQingLars/Monika-IT-bot/commits` since last timestamp
- LLM: OpenRouter — generates PythonPortal-style news article from commit messages
- Stack: aiogram 3.x + gh CLI + openai (AsyncOpenAI for LLM) + httpx (Telegram only)
- News flow: /news → gh fetch new commits → LLM article → post to CHANNEL_ID
- State: ISO timestamp (`commits[0].date`) stored in state/last_event.json for incremental fetch

## Production Lessons
- openai.OpenAI is synchronous — use AsyncOpenAI for async code.
- .env requires python-dotenv to load; always call load_dotenv().
- aiogram 3.x Dispatcher needs dp.bot set manually.
- gh CLI needs `gh auth login` before use.
- GitHub Events API `payload.commits` is NOT included in gh api /users/{user}/events response.
- Use `gh api /repos/{owner}/{repo}/commits?since=<timestamp>` to get commits with full data (sha, message, author, date).
- GitHub Events API `since` param requires ISO 8601 timestamp, NOT event ID.
- Store `commit.committer.date` or `commit.author.date` from commits[0], not event ID.
- If repo returns 404, verify repo name exists with `gh api /repos/{owner}/{repo}`.

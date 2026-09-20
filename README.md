# MonikaNews

Телеграм-бот, который следит за репозиториями FQingLars и публикует новости о новых коммитах в телеграм-канал.

## Как это работает

1. Администратор отправляет команду /news в Telegram.
2. Бот загружает новые коммиты из GitHub через gh CLI.
3. LLM от OpenRouter генерирует конкретную новостную статью в стиле PythonPortal.
4. Статья публикуется в Telegram-канал.

## Установка

```bash
uv sync
cp .env.example .env
python -m monikanews.main
```

## Тесты

```bash
uv run pytest tests/ -v
```

## Стек

- Python 3.12
- aiogram 3.x (Telegram bot)
- gh CLI (GitHub API)
- openai AsyncOpenAI (OpenRouter API)
- httpx (Telegram Bot API)
- python-dotenv

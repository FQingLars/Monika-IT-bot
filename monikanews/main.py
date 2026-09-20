# -*- coding: utf-8 -*-
"""Entry point for MonikaNews Telegram bot."""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from monikanews.bot import create_bot


async def main():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        print("ERROR: BOT_TOKEN is not set in .env", file=sys.stderr)
        sys.exit(1)
    dp = create_bot(bot_token)
    print("MonikaNews bot started.")
    await dp.start_polling(dp.bot)

if __name__ == "__main__":
    asyncio.run(main())

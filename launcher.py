from __future__ import annotations
from al9oo import Al9oo
from discord.utils import setup_logging
from utils.config import discord_api_token

import asyncio
import logging

log = logging.getLogger(__name__)

async def main():
    setup_logging()
    async with Al9oo() as bot:
        await bot.start(discord_api_token)  


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.warning('수동 종료')
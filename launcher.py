from __future__ import annotations
from al9oo import Al9oo
from discord.utils import setup_logging
from utils.configenv import discord_api_token

import asyncio


async def main():
    setup_logging()
    async with Al9oo() as bot:
        await bot.start(token= discord_api_token)  


if __name__ == "__main__":
    asyncio.run(main())
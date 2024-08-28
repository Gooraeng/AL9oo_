from __future__ import annotations
from al9oo import Al9oo
from config import refer_db
from logging.handlers import RotatingFileHandler
from motor.motor_asyncio import AsyncIOMotorClient
from utils.exception import LoadingFailedMongoDrive

import asyncio
import click
import discord
import contextlib
import pathlib
import logging


async def create_pool():
    attempt = 1
    client = AsyncIOMotorClient(refer_db)
    
    while attempt <= 5:
        try:
            response = await client.admin.command('ping')
            if response.get("ok") == 1:
                return client
        except Exception:
            attempt += 1
    raise LoadingFailedMongoDrive


async def main(is_dev : bool = False):
    log = logging.getLogger(__name__)
    try:
        click.echo('')
        pool = await create_pool()
    except LoadingFailedMongoDrive:
        log.exception('Could not set up Mongo. Exiting.')
        return
    
    bot = Al9oo(is_dev) 
    bot.pool = pool

    try:
        await bot.start()  
    except KeyboardInterrupt:
        log.info("KeyboardInterput Detected, shutting down.")
    finally:
        log.info("Closing Resources")
        await bot.close()
    
    log.info('AL9oo shutdown complete.')


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelname == 'WARNING' and 'referencing an unknown' in record.msg:
            return False
        return True


class CustomRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename: str | pathlib.PathLike[str], mode: str = "a", maxBytes: int = 0, backupCount: int = 0, encoding: str | None = None, delay: bool = False, errors: str | None = None) -> None:
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay, errors)
        self.___log = logging.getLogger(__name__)
    
    def doRollover(self) -> None:
        self.___log.warning('로그 파일 경신')
        super().doRollover()  
        

@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        discord.utils.setup_logging()
        # __enter__
        max_bytes = 25 * 1024 * 1024  # 25 MiB
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        log.setLevel(logging.INFO)
        log_data = pathlib.Path(__file__).parent / 'data/al9oo.log'
        handler = CustomRotatingFileHandler(filename=log_data, encoding='utf-8', mode='w', maxBytes=max_bytes, backupCount=5)
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


@click.command()
@click.option('-dev', default=False, help='')
def algoo(dev):
    click.echo('Configuring..')
    with setup_logging():
        asyncio.run(main(dev))
        

if __name__ == "__main__":
    algoo()
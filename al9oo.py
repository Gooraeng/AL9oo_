from __future__ import annotations
from aiohttp import ClientSession
from collections import defaultdict
from datetime import datetime, timedelta
from discord import (
    CustomActivity, 
    Embed,
    ForumChannel,
    Interaction,
    Status, 
    ui,
)
from discord.ext import commands, tasks
from discord.utils import format_dt, utcnow
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any, Optional, Union
from typing_extensions import LiteralString
from config import *
from utils.embed_color import *
from utils.models import ExecutableGuildChannel
from utils.patchnote_manager import PatchNoteManager

import aiofiles
import asyncio
import csv
import discord
import logging


__all__ = (
    "Bot",
)
log = logging.getLogger(__name__)
initial_extensions = (
    'cogs.admin',
    'cogs.feedback',
    'cogs.follow',
    'cogs.get_reference',
    'cogs.patchnote',
    'cogs.utils',
)


def check_data_folder():
    if not os.path.exists('data'):
        os.mkdir('data')


class GuildJoinView(ui.View):
    def __init__(self, guild_id : int = None):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.add_item(
            ui.Button(
                label="Go to Your server!", 
                url=f"https://discord.com/channels/{guild_id}"
            )
        )

    @ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="deleteall")
    async def delete_button(self, interaction : Interaction, button : discord.Button):
        await interaction.message.delete()

    async def on_timeout(self, interaction : Interaction) -> None:
        await interaction.response.send_message(embed=Embed(
            title="Too Late!",
            description="You had about 15 minutes to delete this.\nBut, it seems you are already interested in me!",
            color=failed
        ))
    
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral=True)   


class Al9oo(commands.AutoShardedBot):
    user : discord.ClientUser
    pool : AsyncIOMotorClient
    
    def __init__(self):
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(
            command_prefix=None,
            pm_help=None,
            heartbeat_timeout=60.0,
            chunk_guild_at_startup=False,
            help_command=None,
            intents=intents,
            activity=CustomActivity(name='Listening /help'),
            status=Status.online
        )
        
        self.resumes : defaultdict[int, list[datetime]] = defaultdict(list)
        self.identifies: defaultdict[int, list[datetime]] = defaultdict(list)
        self._auto_info : dict[str, Any] = {}
        self._failed_auto_info : list[str] = []
        self._feedback_channel : Optional[ExecutableGuildChannel] = None
        self._suggestion_channel : Optional[ForumChannel] = None
        self.client_id = int(client_id)

    def load_mongo_drivers(self):
        self.pnote = self.pool["patchnote"]
        # AL9oo 패치노트 로그
        self._pnlog = self.pnote["log"]
        # AL9oo DB renew 시간 갱신
        self._db_renewed = self.pnote["db_renewed"]
        self.fixing = self.pnote["fixing"]

    async def set_feedback_channel(self):
        self._feedback_channel = self.get_channel(int(feedback_log_channel)) or await self.fetch_channel(int(feedback_log_channel))
        self._suggestion_channel = self.get_channel(int(suggestion_channel)) or await self.fetch_channel(int(suggestion_channel))
    
    async def setup_hook(self) -> None:
        self.session = ClientSession()
        check_data_folder()
        self.load_mongo_drivers()
        await self.set_feedback_channel()
        
        PatchNoteManager(self)
        Config(self)
        # 최초 레퍼런스 세팅
        await self.renew_references()
        await self.initial()
        
        log.warning("명령어 로딩 시작")
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                log.info('%s 로딩 완료', extension)
            except Exception as e:
                log.error('%s 로딩 실패\n', extension, exc_info=e)
        log.warning("명령어 로딩 완료")
        
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id
        self.add_view(GuildJoinView())
        
        log.warning("레퍼런스 자동 갱신 백그라운드 실행")
        self.auto_renew_references.start()
        log.warning("오래된 패치노트 정리 백그라운드 실행")
        self.delete_old_patchnote.start()

    @tasks.loop(hours=1)
    async def delete_old_patchnote(self):        
        try:
            threshold_date = utcnow().replace(tzinfo=None) - timedelta(days=365)
            deleted = await self._pnlog.delete_many({"date" : {"$lt" : threshold_date}})
            if deleted.deleted_count != 0:
                log.warning(f"{deleted.deleted_count}개의 오래된 패치노트 삭제 완료")
            return

        except Exception:
            return

    # Bot events
    async def on_ready(self):
        try:
            if self.is_ready():
                if not hasattr(self, 'uptime'):
                    self.uptime = utcnow()
                log.info("[Ready] Tag :  %s // (ID : %s)", self.user, self.user.id)
        
        except Exception as e:
            log.error(e)
            log.error("Force exit")
            await self.close()  

    async def renew_references(self):
        try:
            tasks = []
            urls = [
                [carhunt_db, "carhunt_db.csv"], 
                [clash_db, "clash_db.csv"], 
                [elite_db, "elite_db.csv"], 
                [weekly_db, "weekly_db.csv"]
            ]

            for url, file_name in urls:
                tasks.append(self.db_manage(url, file_name=file_name))
            await asyncio.gather(*tasks)
            
            keys = [
                t[:-8] for s, t in enumerate(self._auto_info.keys())
                if (s + 1) % 2 == 0
            ]
            if keys:
                done = "Renew Success : " + ', '.join(keys)
                log.info(done)
                
            if self._failed_auto_info:
                not_done = "Renew Fail : " + ', '.join(s for s in self._failed_auto_info)
                log.error(not_done)
        
            await self._db_renewed.find_one_and_update({}, {"$set" : self._auto_info})

        except Exception as e:
            log.error(f"Failed AUTOMATICALLY renew DBs due to '{e}'", exc_info=e)
    
    async def db_manage(self, url, *, file_name : Union[LiteralString, str]):
        filename : str = file_name[:-7]
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            async with ClientSession(headers=headers) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise Exception('Download failed.')
                    
                    file_path = os.path.join('data', file_name)
                    with open(file_path, 'w+', encoding='utf-8', newline='') as f:
                        f.write(await resp.text())
                        f.seek(0)
                        reader = csv.reader(f)
                        count = sum(1 for row in reader) - 1

                    _time = format_dt(datetime.now(), style="R")
                    self._auto_info[f"{filename}.count"] = count
                    self._auto_info[f"{filename}.applied"] = _time

        except Exception:
            self._failed_auto_info.append(filename)

    @tasks.loop(minutes=1)
    async def auto_renew_references(self) -> None:
        now = utcnow()
        if now.minute % 15 != 5:
            return
        await self.renew_references()
        await self.initial()
        
    async def initial(self):
        files = [
            'carhunt',
            'clash',
            'elite',
            'weekly'
        ]
        task = [self.process_csv(file) for file in files]
        await asyncio.gather(*task)
    
    async def process_csv(self, file):
        async with aiofiles.open(file=f'./data/{file}_db.csv', mode='r', encoding='utf-8', newline='') as f:
            reader = csv.reader(await f.readlines())
            headers = next(reader)
            data = list(reader)
            
        for header in headers:
            index = headers.index(header)
            values = [row[index] for row in data]
            setattr(self, f"{file}_{header}", values)
        log.info(f"{file} 변수 설정 완료")    
    
    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        return await super().on_error(event_method, *args, **kwargs)
    
    async def start(self):
        await super().start(discord_api_token)
    
    async def close(self):
        await super().close()
        await self.session.close()
    
    @auto_renew_references.before_loop
    @delete_old_patchnote.before_loop
    async def _ready(self):
        await self.wait_until_ready()
    
    @discord.utils.cached_property
    def fb_hook(self):
        target = fwh
        hook = discord.Webhook.from_url(target, client=self)
        return hook

    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner
    
    @property
    def feedback_channel(self) -> Optional[ExecutableGuildChannel]:
        return self._feedback_channel
    
    @property
    def suggestion_channel(self) -> Optional[ForumChannel]:
        return self._suggestion_channel

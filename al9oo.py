from __future__ import annotations
from aiohttp import ClientSession
from datetime import datetime, timedelta
from discord import (
    CustomActivity, 
    Embed, 
    Interaction, 
    Status, 
    ui
)
from discord.ext import commands, tasks
from discord.utils import format_dt, utcnow
from utils.configenv import (
    carhunt_db,
    clash_db,
    elite_db,
    refer_db,
    weekly_db
)
from utils.embed_color import failed
from collections import defaultdict
from motor.motor_asyncio import AsyncIOMotorClient
from utils.patchnote_manager import patchnotemanager
from typing import Any, Union
from typing_extensions import LiteralString

import asyncio
import csv
import discord
import logging
import os



__all__ = (
    "Bot",
)

log = logging.getLogger(__name__)

initial_extensions = (
    'cogs.avatar',
    'cogs.bot_info',
    'cogs.carhuntriot',   
    'cogs.clubclash',
    'cogs.elite',
    'cogs.get_announcements',
    'cogs.help',
    'cogs.patchnote_manage',
    'cogs.patchnote_view',
    'cogs.redeem',
    'cogs.releasenote',
    'cogs.support',
    'cogs.sync',
    'cogs.system_info',
    'cogs.weeklycompetition'
)



class GuildJoinView(ui.View):
    def __init__(self, guild_id : int = None):
        super().__init__(timeout= None)
        self.guild_id = guild_id
        self.add_item(ui.Button(label= "Go to Your server!", url= f"https://discord.com/channels/{guild_id}", row= 0))


    @ui.button(label= "Delete", style= discord.ButtonStyle.danger, custom_id= "deleteall")
    async def delete_button(self, interaction : Interaction, button : discord.Button):
        try:
            await interaction.message.delete()
        
        except:
            await interaction.response.defer(thinking= True, ephemeral= True)
            await asyncio.sleep(4)
            await interaction.followup.send("Cannot delete this message. I suppose there is something problem.\nPlease try again later.")


    async def on_timeout(self, interaction : Interaction) -> None:
        await interaction.response.send_message(embed= Embed(
            title = "Too Late!",
            description= "You had about 15 minutes to delete this.\
                \nBut, it seems you are already interested in me!",
            color= failed
        ))
        
    
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral= True)   
        


class Al9oo(commands.Bot):
    user : discord.ClientUser
    
    def __init__(self):
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(
            command_prefix= None,
            pm_help= None,
            heartbeat_timeout= 60.0,
            chunk_guild_at_startup= False,
            help_command= None,
            intents= intents,
        )
        self._client_2 = AsyncIOMotorClient(refer_db)
        # 레퍼관련
        self.pnote = self._client_2["patchnote"]
        self._pnlog = self.pnote["log"]
        self._db_renewed = self.pnote["db_renewed"]
        self.fixing = self.pnote["fixing"]
        self.resumes : defaultdict[int, list[datetime]] = defaultdict(list)
        self.identifies: defaultdict[int, list[datetime]] = defaultdict(list)
        self._auto_info : dict[str, Any] = {}; self._failed_auto_info : list[str] = []
        # self._feedback_log_channel_id = feedback_log_channel
        # self._feedback_log_channel = self.get_channel(int(self._feedback_log_channel_id))


    def check_data_folder(self) -> None:
        if not os.path.exists('data'):
            os.mkdir('data')


    async def setup_hook(self) -> None:
        self.check_data_folder()
        
        log.warning("아9 패치노트 로딩")
        patchnotemanager.process.start()
        self.auto_renew_references.start()
        await self.renew_references()
        
        log.warning("명령어 로딩 시작")
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception:
                log.exception('%s 로딩 실패', extension)
        log.info("명령어 로딩 완료")
        
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id
        self.add_view(GuildJoinView())
        
        log.warning("패치노트 정리 백그라운드 실행")
        self.delete_old_patchnote.start()


    @tasks.loop(minutes= 10)
    async def delete_old_patchnote(self):
        await self.wait_until_ready()
        if self.is_closed():
            return
        
        try:
            threshold_date = datetime.now() - timedelta(days= 365)
            deleted = await self._pnlog.delete_many({"date": {"$lt": threshold_date}})
            if deleted.deleted_count != 0:
                log.info(f"오래된 패치노트 데이터 삭제 완료")
            return

        except Exception:
            return


    # Bot events
    async def on_ready(self):
        try:
            if self.is_ready():
                if not hasattr(self, 'uptime'):
                    self.uptime = utcnow()
                activity = CustomActivity(name= f'{len(self.guilds)} Server(s) | /help')
                await self.change_presence(activity= activity, status= Status.online)
                log.info("[Ready] Tag :  %s // (ID : %s)", self.user, self.user.id)
        
        except Exception as e:
            log.error(e)
            log.error("Force exit")
            await self.close()
    
    
    async def on_shard_resumed(self, shard_id: int):
        self.resumes[shard_id].append(utcnow())    


    async def on_guild_join(self, guild : discord.Guild):
        try:
            current_status = discord.CustomActivity(name= f'{len(self.guilds)} Server(s) | /help')
            await self.change_presence(status= discord.Status.online, activity= current_status)
            
            # Welcome Message - Could be added in future
            # embed_join = Embed(
            #     title= "Advanced Discord Bot that provides various Reference Runs!",
            #     description= f"I am happy to join **[ {guild.name} ]** server!", color= al9oo_point
            # )
            # embed_join.set_thumbnail(url= self.user.avatar.url)
            # embed_join.add_field(name= "* Let's taste `/help` first to close to me!", value= "", inline= False)

            # view = GuildJoinView(guild_id= guild.id)
            # await guild.owner.send(content= "", embed= embed_join, view= view, file= File("images/WELCOME.png"))
        
        except Exception as e:
            log.error(e)


    async def on_guild_remove(self, guild : discord.Guild):
        try:      
            current_status = CustomActivity(name= f'{len(self.guilds)} Server(s) | /help')
            await self.change_presence(status= Status.online, activity= current_status)

        except Exception as e:
            log.error(e)


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
                tasks.append(self.db_manage(url= url, file_name= file_name))
            await asyncio.gather(*tasks)
            
            keys = [
                t[:-8] for s, t in enumerate(self._auto_info.keys())
                if (s + 1) % 2 == 0
            ]
            msg = "Renew Success : " + ', '.join(keys)
            log.info(msg)
            
            if self._failed_auto_info:
                not_done = "Renew Fail : " + ', '.join(s for s in self._failed_auto_info)
                log.error(not_done)
            
            await self._db_renewed.find_one_and_update({}, {"$set" : self._auto_info})

        except Exception as e:
            log.error(f"Failed AUTOMATICALLY renew DBs due to '{e}'")

    
    async def db_manage(self, url, file_name : Union[LiteralString, str]):
        db_write = None
        count = None
        filename : str = file_name[:-7]
        headers = {'User-Agent': 'Mozilla/5.0'}

        async with ClientSession(headers= headers) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    file_path = os.path.join('data', file_name)
                    with open(file_path, 'w+', encoding= 'utf-8', newline= '') as f:
                        f.write(await resp.text())
                        f.seek(0)
                        reader = csv.reader(f)
                        count = sum(1 for row in reader) - 1
                    db_write = True
    
        if db_write:
            _time = format_dt(datetime.now(), style= "R")
            self._auto_info[f"{filename}.count"] = count
            self._auto_info[f"{filename}.applied"] = _time
        else:
            self._failed_auto_info.append(filename)
        

    @tasks.loop(minutes= 1)
    async def auto_renew_references(self) -> None:
        now = utcnow()
        if now.minute % 15 != 5:
            return
        
        await self.renew_references()


    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner
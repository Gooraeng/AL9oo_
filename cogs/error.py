from __future__ import annotations
from bson import ObjectId
from datetime import datetime, timedelta
from discord import app_commands, Embed, File, Interaction
from discord.ext import commands, tasks
from discord.utils import format_dt
from typing import Optional, TYPE_CHECKING
from utils.embed_color import etc
from utils.exception import FeedbackButtonOnCooldown
from utils.models import ErrorLogTrace, NumberedObject

if TYPE_CHECKING:
    from al9oo import Al9oo

import asyncio
import discord
import inspect
import io
import logging
import traceback
import sys


log = logging.getLogger(__name__)


class AppCommandErrorHandler(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.lg = self.app.pool['Feedback']['trace']
        self.default_message = "An error occurred. Please try again later or consider to contact support."
        self.error_report.start()

    async def cog_load(self) -> None:
        tree = self.app.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error
        
    async def on_app_command_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        error_time = interaction.created_at
        embed = Embed(title='', description='', color=etc, timestamp=error_time)
        
        if isinstance(error, FeedbackButtonOnCooldown):
            until = error_time + timedelta(seconds=error.retry_after)
            until = format_dt(until, 'T')
            
            embed.title = 'Do not spam that button.'
            embed.description = f'You had submitted 2 feedbacks before, so you were temporarily blocked until {until}.'
            embed.add_field(
                name='Why am I blocked?',
                value=inspect.cleandoc(
                    """
                    The reason is How we receive your feedback.
                    We are collecting them via Webhook, and it has ratelimit that prevents it from being spammed abnormally.
                    That's why you have 5 minute cooldown is imposed per 2 submissions.
                    We deeply appreciate your patience.
                    """
                )
            )
            
        elif isinstance(error, app_commands.CommandOnCooldown):
            retry_after = error_time + timedelta(seconds=error.retry_after)
            retry_after = format_dt(retry_after, 'T')
            
            embed.title = 'Please Be Patient!'
            embed.description = f'You are temporarily blocked using </{interaction.command.qualified_name}:{interaction.data["id"]}> again until {retry_after}'
            
        elif isinstance(error, app_commands.BotMissingPermissions):
            missing_list = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]
            missing = "\n* ".join(s for s in missing_list)
            if interaction.user.guild_permissions.manage_roles:
                embed.description= "Please check interact channel's permission(s)!"
            else:
                embed.description = "Please Contact Server Moderator you are in to fix permission(s)!"
            embed.add_field(name="Missing Permission(s)", value=f"* {missing}")
            
        elif isinstance(error, app_commands.CommandInvokeError):
            e = error.original
            embed.title = "Failed to invoke command."
            embed.description = inspect.cleandoc(
                f"""
                * Error Type : {e.__class__.__name__}
                * Error Summary : {e}
                * Command : {error.command.qualified_name}
                Please run it again. If you are countinuing get failuare, consider to report with `/feedback` command.
                """
            )
        embed.set_footer(text='This incident will be automatically reported.')
        await self.send_error(interaction, embed=embed, error=error)
    
    async def send_error(self, interaction : Interaction, *, embed : Embed, error : Exception):
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass
        # Do not handle about discord server error
        if isinstance(error, discord.DiscordServerError):
            return
        
        await self.configure_error(error, error_time=interaction.created_at)

    async def configure_error(self, error : Exception, *, error_time : Optional[datetime] = None):
        trace = traceback.format_exception(None, error, error.__traceback__)
        formatted_trace = "".join(trace)
        log.error(f'Error : {error}\nTraceback :\n{formatted_trace}')
        
        error_info = ErrorLogTrace(
            error_type=error.__class__.__name__,
            detected_at=error_time,
            details=formatted_trace
        ).model_dump(exclude={'id'})
        
        while True:
            result = await self.lg.insert_one(error_info)
            if result.acknowledged:
                return
            await asyncio.sleep(1)

    @tasks.loop(minutes=1)
    async def error_report(self):
        def formatted_time(now : Optional[float] = None):
            if not now:
                now = discord.utils.utcnow().timestamp()
            return f'{datetime.fromtimestamp(now).strftime("%Y/%m/%d %H:%M:%S")} (UTC)'
        
        data = await self.lg.find({}).sort('detected_at', 1).to_list(length=150)
        if not data or len(data) == 0:
            return
        
        errors = [ErrorLogTrace(**doc) for doc in data]        
        files : list[NumberedObject] = []
        max_file_size = 25 * 1024 * 1024

        for i in errors: 
            log_detail = inspect.cleandoc(
                f"""
                * SENT AT : {formatted_time()}
                * ERROR TYPE : {i.error_type}
                * DETECTED AT : {formatted_time(i.detected_at)}
                """
            )
            trace = f'{log_detail}\n\n{i.details}'
            fp = io.BytesIO(trace.encode())
            file = File(fp, filename=f'error-log-{int(i.detected_at*1000)}.txt')
            
            if sys.getsizeof(file) < max_file_size:
                files.append(NumberedObject(_id=i.id, object=file))      

        done : list[ObjectId] = []
        failed : list[ObjectId] = []
        
        per_send = 10
        for i in range(0, len(files), per_send):
            temp_files = files[i:+i+per_send]
            files = [f.object for f in temp_files if isinstance(f.object, discord.File)]
            object_ids = [s.id for s in temp_files]
            try:
                await self.app.el_hook.send(files=files)
                done += object_ids
            except Exception as e:
                failed += object_ids
                log.error('에러 로그 전송 실패 : %s 발생 // 건너뜀.', e.__class__.__name__)
                continue
            finally:
                if len(done) + len(failed) >= len(files):
                    break
                await asyncio.sleep(2.5)
        
        if len(done) > 0:
            log.info("오류 정보 총 %s개 전송 완료", len(done))
            result = await self.lg.delete_many({'_id' : {'$in' : done}})
            log.info("전송된 오류 정보 총 %s개 삭제 완료", result.deleted_count)
        if len(failed) > 0:
            log.error("오류 총 %s개 전송 실패", len(failed))
            
    @error_report.before_loop
    async def ready(self):
        await self.app.wait_until_ready()


async def setup(app : Al9oo):
    await app.add_cog(AppCommandErrorHandler(app))
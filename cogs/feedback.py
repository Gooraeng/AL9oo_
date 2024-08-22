from __future__ import annotations
from datetime import timedelta, timezone
from discord import app_commands, Embed, Interaction
from discord.ext import commands, tasks
from discord.utils import format_dt, utcnow
from typing import TYPE_CHECKING
from utils.commandpermission import permissioncheck
from utils.embed_color import succeed, failed, interaction_with_server
from utils.exception import key
from utils.feedback import FeedbackView, FeedbackFailedView
from utils.models import (
    FeedbackToMongo,
    FeedbackAllInfo,
)
from utils.paginator import FeedbackPagination

if TYPE_CHECKING:
    from al9oo import Al9oo

import asyncio
import discord
import inspect
import logging


log = logging.getLogger(__name__)
cooldown = 60


def check_owner(interaction : Interaction):
    if interaction.user.id == 303915314062557185:
        return None
    return app_commands.Cooldown(1, cooldown)


def response_err_detecter(code : int) -> str:
    if code == 304 :
        return "NOT MODIFIED : 	The entity was not modified (no action was taken)."
    elif code == 400 :
        return "BAD REQUEST : The request was improperly formatted, or the server couldn't understand it."
    elif code == 401 :
        return "UNAUTHORIZED : The Authorization header was missing or invalid."
    elif code == 403 :
        return "FORBIDDEN : My problem."
    elif code == 404:
        return "NOT FOUND : My problem."
    elif code == 429 :
        return "TOO MANY REQUESTS : I think someone is spamming somehow."
    elif code >= 500:
        return "DISCORD SERVER ERROR : It's not what I can handle with."
    else:
        return str(code)
    

class Feedback(commands.Cog): 
    
    global cooldown
       
    def __init__(self, app : Al9oo) :
        self.app = app
        self.fb = self.app.pool['Feedback']['temp']
        self.cd = commands.CooldownMapping.from_cooldown(2, 300, key)
        self.check_feedbacks.start()
    
    async def feedback_handler(self, view : FeedbackView, *, interaction : Interaction, embed : Embed):
        response_code = None

        response = view.modal_responses
        feedback_info = Embed(
            title=response.title,
            description=response.detail,
            color=interaction_with_server,
            timestamp=utcnow()
        )
        if interaction.guild:
            feedback_info.add_field(name='Guild', value=f'{interaction.guild} ({interaction.guild.id})')
        else:
            feedback_info.add_field(name='Channel', value=f'DM ({interaction.user.dm_channel.id})')
        feedback_info.add_field(name='Author', value=f'{interaction.user} ({interaction.user.id})')
        
        attempts = 1
        while attempts <= 3:
            try:
                created_at = utcnow()
                info = FeedbackToMongo(
                    type=response.title,
                    detail=response.detail,
                    author_info=FeedbackAllInfo.from_interaction(interaction),
                    created_at=created_at
                ).model_dump()

                await self.fb.insert_one(info)
                
            except discord.Forbidden as e:
                response_code = e.code or e.status
                break
            
            except discord.HTTPException as e:
                try_later = 2 * (attempts - 1) + 3
                response_code = e.code or e.status
                embed.title = 'Your Feedback was rejected!'
                embed.description = f'Sorry, We had Internet problem while processing your feedback.\nWe are trying to send your feedback again in {try_later} seconds.'
                embed.color = failed
                embed.add_field(name=f'CURRENT ATTEMPTS', value=f'{attempts} / {3}')
                await view.message.edit(embed=embed)
                await asyncio.sleep(try_later)
                attempts += 1
            
            else:
                embed.title = 'Your Feedback was Submitted!'
                embed.description = inspect.cleandoc(
                    f"""
                    Developer will take a look.
                    However, please consider possiblity your opinions could not be approved.
                    We would like to ask for your understanding.
                    
                    Submitted at : {format_dt(created_at, 'F')}
                    """
                )
                embed.colour = succeed
                embed.clear_fields()
                await view.message.edit(embed=embed)
                break
                
        if not response_code:
            return

        reason = response_err_detecter(response_code)
        instruction = inspect.cleandoc(
            """
                we would like to request you press button below so you copy what you wrote.
                And please consider to post it at suggestion channel in AL9oo Server.
            """
        )
        embed.description = f"I'm sorry. I tried hard to send your feedback, but, ultimately failed.\n[Reason] {reason}\nAlternatively, {instruction}"
        other_view = FeedbackFailedView(view.modal_responses, user_id=interaction.user.id)
        await view.message.edit(view=other_view, embed=embed)     

    @app_commands.command(
        name='feedback',
        description='Is there any feedback to send to us?',
        extras={"permissions" : ["Embed Links"]}
    )
    @app_commands.guild_only()
    @app_commands.checks.dynamic_cooldown(check_owner, key=lambda i : i.user.id)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def feedback(self, interaction : Interaction):   
        await interaction.response.defer(thinking=True, ephemeral=True)

        retry_after = interaction.created_at + timedelta(seconds=cooldown)
        view = FeedbackView(interaction.user.id, delete_time=retry_after, cooldownMapping=self.cd)
        
        embed = view.load_warning_embed(True)
        embed.description += '\n### Plus, you are allowed to submit up to 2 feedbacks in 5 minutes.'
        cooltime = self.cd.get_bucket(interaction).get_retry_after()
        if cooltime:
            until = interaction.created_at + timedelta(seconds=cooltime)
            until = format_dt(until, 'T')
            embed.add_field(name='WARNING', value=f'You are not able to send feedback until {until}')
        
        view.message = await interaction.edit_original_response(content=None, embed=embed, view=view)
        await view.wait()
        
        if view.is_pressed:
            self.cd.update_rate_limit(interaction)
        
        await self.feedback_handler(view, interaction=interaction, embed=embed)
        
    @feedback.error
    async def feedback_err(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            embed_cd_error = Embed(
                title='Oops! Please be patient!',
                description=f'You can execute {int(error.retry_after)} seconds later!',
                colour=failed
            )
            await interaction.response.send_message(embed=embed_cd_error, delete_after=10, ephemeral=True)
        
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction, error=error)
        
        if isinstance(error, app_commands.CheckFailure):
            pass
        
        else: raise error

    @tasks.loop(minutes=1)
    async def check_feedbacks(self):
        data = await self.fb.find({}).sort('created_at' , 1).to_list(length=None)
        feedbacks = [FeedbackToMongo(**{k: v for k, v in doc.items() }) for doc in data]
        if not feedbacks or len(feedbacks) == 0:
            return
        
        embeds = []
        per_page = 5
        for i in range(0, len(feedbacks), per_page):
            temp = feedbacks[i:i+per_page]
            temp_list : list[Embed] = []
            for j in temp:
                embed = Embed(
                    title=f"[{j.type}] FEEDBACK",
                    description=f'{j.detail}\n\nCreated at : {format_dt(j.created_at.astimezone(timezone.utc), 'F')}',
                    color=interaction_with_server,
                )
                num = 1
                author_info = j.author_info
                if author_info.guild:
                    embed.add_field(name=f'{num}. Guild', value=f'* name : {author_info.guild.name}\n* id : {author_info.guild.id}')
                    num += 1
                if author_info.channel:
                    embed.add_field(name=f"{num}. Channel", value=f'* name : {author_info.channel.name}\n* id : {author_info.channel.id}')
                    num += 1
                embed.add_field(name=f"{num}. Author", value=f'* name : {author_info.author.name}\n* id : {author_info.author.id}')
                temp_list.append(embed)
            embeds.append(temp_list)
        
        view = FeedbackPagination(embeds, self.app.fb_hook)
        try:
            await view.start()
            log.info("피드백 %s개 전송 완료", len(data))

        except:
            return
        
        if data or len(data) > 0:
            ids = [doc['_id'] for doc in data]
            result =await self.fb.delete_many({'_id' : {'$in' : ids}})
            log.info("전송된 피드백 %s개 삭제 완료", result.deleted_count)

    @check_feedbacks.before_loop
    async def ready(self):
        await self.app.wait_until_ready()


async def setup(app : Al9oo):
    await app.add_cog(Feedback(app))
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from discord import (
    app_commands,
    ButtonStyle,
    ComponentType,
    Embed, 
    Interaction,
    InteractionMessage,
    PartialEmoji,
    TextStyle,
    ui,
)
from discord.ext import commands, tasks
from discord.utils import format_dt, utcnow
from typing import Any, Optional, TYPE_CHECKING
from utils.commandpermission import permissioncheck
from utils.embed_color import succeed, failed, interaction_with_server
from utils.exception import key
from utils.models import (
    ModalResponse, 
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
import re

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
    

class FeedbackProblemModal(ui.Modal):
    def __init__(
        self, 
        title : Optional[str] = None,
        *,
        user_id : Optional[int] = None,
        user_input : Optional[str] = None,
        view : Optional[FeedbackViewBase] = None,
        failed_feedback : bool = False
    ) -> None:
        
        self.failed_feedback = failed_feedback
        self.user_input = user_input
        self.view = view
        
        if not title:
            title = 'TITLE IS MISSING'
            
        default = None if user_input is None else user_input
        custom_id = f'problem_modal:user:{user_id}' if user_id else None
            
        super().__init__(
            title=title,
            timeout=None,
            custom_id=custom_id
        )
        
        self.details = ui.TextInput(
            label='Details',
            placeholder='Please Fill out here.',
            required=True,
            default=default,
            min_length=10,
            max_length=400,
            style=TextStyle.paragraph
        )
        self.add_item(self.details)
    
    def clear(self):
        self.details.default = None
    
    async def on_submit(self, interaction: Interaction):
        self.interaction = interaction
        if not self.failed_feedback:
            self.view.modal_responses = ModalResponse(
                title=self.title,
                detail=self.details.value
            )
            await self.view.rebind(interaction)
        self.stop()
    
    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        return await super().on_error(interaction, error)

    
class FeedbackViewBase(ui.View):
    def __init__(self, user_id : Optional[int] = None, modal_responses : Optional[ModalResponse] = None):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.modal_responses : Optional[ModalResponse] = modal_responses
        self.message : Optional[InteractionMessage] = None
        
    @property
    def modal_responses(self) -> Optional[ModalResponse]:
        return self._modal_responses

    @modal_responses.setter
    def modal_responses(self, value : Optional[ModalResponse]):
        self._modal_responses = value
    
    def adjust_buttons(self):
        """입맛대로 사용하셈"""
        pass
    
    def setup_button_custom_id(self, user_id : Optional[int] = None, /):
        if not user_id:
            return
        
        for item in self.children:
            assert item.type == ComponentType.button
            label = re.sub(r'\s+', '', item.label)
            item.custom_id = f'{self.__class__.__name__}:{label}:{user_id}'
    
    def load_warning_embed(self, load : Optional[bool] = None, /) -> Embed:
        embed = Embed(colour=interaction_with_server)
        if load:
            embed.title = '❗ Warning'
            embed.description = inspect.cleandoc(
                """
                You are unable to cancel in the middle of sending feedback.
                Please press one of buttons to proceed what problem you would like to report.
                """ 
            ) + "\n### [COMMAND COOLDOWN STATUS]\n:"
        return embed

    def clear_buttons(self):
        for item in self.children:
            assert item.type == ComponentType.button
            self.remove_item(item)
        return self
    
    async def rebind(self, interaction : Interaction):
        pass
    
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await super().on_error(interaction, error, item)
    
    async def on_timeout(self) -> None:
        self.clear_items()
        
        if self.message:
            try:
                await self.message.delete()
            except:
                pass

      
class FeedbackFailedView(FeedbackViewBase):
    def __init__(
        self,
        responses : Optional[ModalResponse] = None,
        *,
        user_id : Optional[int] = None,
        instruction : Optional[str] = None
    ):
        super().__init__(user_id=user_id)
        self.adjust_buttons(True)
        self.modal_responses = responses 
        self.__modal = FeedbackProblemModal(
            responses.title,
            user_id=user_id,
            user_input=responses.detail,
            view=self,
            failed_feedback=True
        )
        self._al9oo_server = ui.Button(label="AL9oo Server", url='https://discord.gg/8dpAFYXk8s', row=0)
        self.instruction_embed(instruction)
        self.check_embed()
        
    def instruction_embed(self, instruction : str, /):
        embed = self.load_warning_embed()
        embed.description = instruction
        self.inst_embed = embed
    
    def check_embed(self):
        embed = self.load_warning_embed()
        embed.title = 'Did you copy all text?'
        embed.description = inspect.cleandoc(
            """
                You may close this message If you did.
                If you want to watch direction, press "Direction" button.
            """
        )   
        self.chec_embed = embed
    
    def adjust_buttons(self, initial : bool = False):
        self.clear_items()
        self.add_item(self.get_feedback)
        if not initial:
            self.add_item(self.direction)
            self.add_item(self._al9oo_server)
        self.setup_button_custom_id(self.user_id)
        
    @ui.button(label='Get yours!', style=ButtonStyle.green, emoji=PartialEmoji(name='🔎'))
    async def get_feedback(self, interaction : Interaction, _):
        await interaction.response.send_modal(self.__modal)
        await interaction.response.edit_message(embed=self.chec_embed, view=self)
        
    @ui.button(label='Direction', style=ButtonStyle.grey, emoji=PartialEmoji(name='\N{PUSHPIN}'))
    async def direction(self, interaction : Interaction, _):
        await interaction.response.edit_message(view=self, embed=self.inst_embed)
        
    async def interaction_check(self, interaction: Interaction) -> bool:
        if self.modal_responses.detail:
            return True
        
        await interaction.response.send_message('OMG.. We lost your feedback. We deeply apologize for it.', ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        return await super().on_timeout()
    
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await super().on_error(interaction, error, item)


class FeedbackView(FeedbackViewBase):
    def __init__(
        self,
        user_id : Optional[int] = None,
        *,
        delete_time : Optional[datetime] = None,
        cooldownMapping : Optional[commands.CooldownMapping] = None
    ):
        super().__init__(user_id=user_id)
        self.cd = cooldownMapping
        self.delete_time = delete_time
        self.user_id = user_id
        self.adjust_buttons(True)
        self.is_pressed = False

    def adjust_buttons(self, reset : bool = False, /):
        self.clear_buttons()
        if reset:
            self.add_item(self.bug_report)
            self.add_item(self.suggestion)
            self.add_item(self.others)
        else:
            self.add_item(self.edit)
            self.add_item(self.reset)
            self.add_item(self.send)
            
        self.setup_button_custom_id(self.user_id)
        
    def load_warning_embed(self, load : Optional[bool] = None, /) -> Embed:
        embed = super().load_warning_embed(load)
        
        if load:
            if self.delete_time and self.delete_time.timestamp() > utcnow().timestamp():
                embed.description += f" {format_dt(self.delete_time, 'R')}"
            else:
                embed.description += " AVAILABLE"
        return embed
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        cooltime = self.cd.get_bucket(interaction).get_retry_after()
        if cooltime:
            until = interaction.created_at + timedelta(seconds=cooltime)
            until = format_dt(until, 'T')
            embed = Embed(
                title='Do not spam frequently',
                description=f'You had submitted 2 feedbacks before, so you were temporarily blocked until {until}.',
                color=failed
            )
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
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    async def rebind(self, interaction : Interaction):
        self.adjust_buttons()
        embed = super().load_warning_embed()
        embed.title = 'Please CHECK before submission.'
        embed.description = f'### {self.modal_responses.title}\n{self.modal_responses.detail}'
        embed.set_footer(text='Press button you want.\nIf you decided to submit, then you will have cooldown for 5 minutes for preventing spam.')
        await interaction.response.edit_message(view=self, embed=embed)
    
    async def spawn_modal(self, interaction : Interaction, modal_title : str):
        self.clear_items()
        modal = FeedbackProblemModal(modal_title, user_id=self.user_id, view=self)
        await interaction.response.send_modal(modal)
    
    @ui.button(label='Bug Report', style=ButtonStyle.danger, emoji=PartialEmoji(name='\N{BUG}'))
    async def bug_report(self, interaction : Interaction, _):
        await self.spawn_modal(interaction, self.bug_report.label)
        
    @ui.button(label='Suggestion', style=ButtonStyle.primary, emoji=PartialEmoji(name='\N{ELECTRIC LIGHT BULB}'))
    async def suggestion(self, interaction : Interaction, _):
        await self.spawn_modal(interaction, self.suggestion.label)
    
    @ui.button(label='Others', style=ButtonStyle.grey, emoji=PartialEmoji(name='🔎'))
    async def others(self, interaction : Interaction, _):
        await self.spawn_modal(interaction, self.others.label)
    
    @ui.button(label='Edit', style=ButtonStyle.danger, emoji=PartialEmoji(name='\N{MEMO}'))
    async def edit(self, interaction : Interaction, _):
        title = self.modal_responses.title
        detail = self.modal_responses.detail
        modal = FeedbackProblemModal(
            title,
            user_id=interaction.user.id,
            user_input=detail,
            view=self
        )
        await interaction.response.send_modal(modal)
    
    @ui.button(label='Reset', style=ButtonStyle.gray, emoji=PartialEmoji(name='✂️'))   
    async def reset(self, interaction : Interaction, _):
        embed = self.load_warning_embed(True)
        self.modal_responses = None
        self.adjust_buttons(True)
        await interaction.response.edit_message(view=self, embed=embed) 
    
    @ui.button(label='Send', style=ButtonStyle.green, emoji=PartialEmoji(name='\N{INCOMING ENVELOPE}'))
    async def send(self, interaction : Interaction, _): 
        embed = super().load_warning_embed()
        embed.title = 'Waiting For Sending...'
        embed.description = 'This will be done shortly. Please wait...'
        await interaction.response.edit_message(embed=embed, view=None)
        self.is_pressed = True
        self.stop()
        
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        await super().on_error(interaction, error, item)
    
    async def on_timeout(self) -> None:
        await super().on_timeout()


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
        embed.description = f"I'm sorry. I tried hard to send your feedback, but, ultimately failed.\n[Reason] {reason}\nAlternatively," + instruction
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
from __future__ import annotations
from al9oo import Al9oo
from discord.ext import commands
from typing import Any, Optional
from utils.embed_color import failed, interaction_with_server
from utils.exception import FeedbackButtonOnCooldown
from utils.models import ModalResponse
from .view import BaseView

import datetime
import discord
import inspect
import re


class FeedbackProblemModal(discord.ui.Modal):
    def __init__(
        self, 
        title : Optional[str] = None,
        *,
        user_input : Optional[str] = None,
        bot : Optional[Al9oo] = None,
        view : Optional[FeedbackViewBase] = None,
        failed_feedback : bool = False
    ) -> None:
        self.app = bot
        self.failed_feedback = failed_feedback
        self.user_input = user_input
        self.view = view
        
        if not title:
            title = 'TITLE IS MISSING'
            
        default = None if user_input is None else user_input
            
        super().__init__(
            title=title,
            timeout=None,
        )
        
        self.details = discord.ui.TextInput(
            label='Details',
            placeholder='Please Fill out here.',
            required=True,
            default=default,
            min_length=10,
            max_length=250,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.details)
    
    def clear(self):
        self.details.default = None
    
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        if not self.failed_feedback:
            self.view.modal_responses = ModalResponse(
                title=self.title,
                detail=self.details.value
            )
            await self.view.rebind(interaction)
        self.stop()
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        embed = discord.Embed(
            title='Unknown Error Occured',
            description=inspect.cleandoc(
                """
                We are sorry, this error was automatically reported to AL9oo Management Team.
                But, We don't investigate about Discord's fault. We appreciate to your patience.
                """
            ),
            color=failed
        )
        await self.app.err_handler.send_error(interaction, embed=embed, error=error)


class FeedbackViewBase(BaseView):
    def __init__(self, bot : Al9oo, user_id : Optional[int] = None, modal_responses : Optional[ModalResponse] = None):
        super().__init__(bot=bot, timeout=None)
        self.user_id = user_id
        self.modal_responses : Optional[ModalResponse] = modal_responses
        self.message : Optional[discord.InteractionMessage] = None
        
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
        """
        Sets up button custom ids like\n
        `{View class name}:{button_label}:{interaction user id}`
        """
        if not user_id:
            return
        
        for item in self.children:
            assert item.type == discord.ComponentType.button
            label = re.sub(r'\s+', '', item.label)
            item.custom_id = f'{self.__class__.__name__}:{label}:{user_id}'
    
    def load_warning_embed(self, load : Optional[bool] = None, /) -> discord.Embed:
        embed = discord.Embed(colour=interaction_with_server)
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
            assert item.type == discord.ComponentType.button
            self.remove_item(item)
        return self
    
    async def rebind(self, interaction : discord.Interaction):
        pass
    
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[Any]) -> None:
        return await super().on_error(interaction, error, item)
    
    async def on_timeout(self) -> None:
        if self.message:
            try:
                await self.message.delete()
            except:
                await self.message.edit(view=None)

      
class FeedbackFailedView(FeedbackViewBase):
    def __init__(
        self,
        responses : Optional[ModalResponse] = None,
        *,
        bot : Al9oo,
        user_id : Optional[int] = None,
        instruction : Optional[str] = None
    ):
        super().__init__(bot=bot, user_id=user_id)
        self.adjust_buttons(True)
        self.modal_responses = responses 
        self.__modal = FeedbackProblemModal(
            responses.title,
            user_input=responses.detail,
            view=self,
            failed_feedback=True
        )
        self._al9oo_server = discord.ui.Button(label="AL9oo Server", url='https://discord.gg/8dpAFYXk8s', row=0)
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
        
    @discord.ui.button(label='Get yours!', style=discord.ButtonStyle.green, emoji=discord.PartialEmoji(name='🔎'))
    async def get_feedback(self, interaction : discord.Interaction, _):
        await interaction.response.send_modal(self.__modal)
        await interaction.response.edit_message(embed=self.chec_embed, view=self)
        
    @discord.ui.button(label='Direction', style=discord.ButtonStyle.grey, emoji=discord.PartialEmoji(name='\N{PUSHPIN}'))
    async def direction(self, interaction : discord.Interaction, _):
        await interaction.response.edit_message(view=self, embed=self.inst_embed)
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.modal_responses.detail:
            return True
        
        await interaction.response.send_message('OMG.. We lost your feedback. We deeply apologize for it.', ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        return await super().on_timeout()
    
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[Any]) -> None:
        return await super().on_error(interaction, error, item)


class FeedbackView(FeedbackViewBase):
    def __init__(
        self,
        user_id : Optional[int] = None,
        *,
        bot : Al9oo,
        delete_time : Optional[datetime.datetime] = None,
        cooldownMapping : Optional[commands.CooldownMapping] = None
    ):
        super().__init__(user_id=user_id)
        self.app = bot
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
        
    def load_warning_embed(self, load : Optional[bool] = None, /) -> discord.Embed:
        embed = super().load_warning_embed(load)
        
        if load:
            if self.delete_time and self.delete_time.timestamp() > discord.utils.utcnow().timestamp():
                embed.description += f" {discord.utils.format_dt(self.delete_time, 'R')}"
            else:
                embed.description += " AVAILABLE"
        return embed
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        cooltime = self.cd.get_bucket(interaction).get_retry_after()
        if cooltime:
            raise FeedbackButtonOnCooldown(cooltime)
        return True

    async def rebind(self, interaction : discord.Interaction):
        self.adjust_buttons()
        embed = super().load_warning_embed()
        embed.title = 'Please CHECK before submission.'
        embed.description = f'### {self.modal_responses.title}\n{self.modal_responses.detail}'
        embed.set_footer(text='Press button you want.\nIf you decided to submit, then you will have cooldown for 5 minutes for preventing spam.')
        await interaction.response.edit_message(view=self, embed=embed)
    
    async def spawn_modal(self, interaction : discord.Interaction, modal_title : str):
        self.clear_items()
        modal = FeedbackProblemModal(modal_title, view=self, bot=self.app)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Bug Report', style=discord.ButtonStyle.danger, emoji=discord.PartialEmoji(name='\N{BUG}'))
    async def bug_report(self, interaction : discord.Interaction, _):
        await self.spawn_modal(interaction, self.bug_report.label)
        
    @discord.ui.button(label='Suggestion', style=discord.ButtonStyle.primary, emoji=discord.PartialEmoji(name='\N{ELECTRIC LIGHT BULB}'))
    async def suggestion(self, interaction : discord.Interaction, _):
        await self.spawn_modal(interaction, self.suggestion.label)
    
    @discord.ui.button(label='Others', style=discord.ButtonStyle.grey, emoji=discord.PartialEmoji(name='🔎'))
    async def others(self, interaction : discord.Interaction, _):
        await self.spawn_modal(interaction, self.others.label)
    
    @discord.ui.button(label='Edit', style=discord.ButtonStyle.danger, emoji=discord.PartialEmoji(name='\N{MEMO}'))
    async def edit(self, interaction : discord.Interaction, _):
        title = self.modal_responses.title
        detail = self.modal_responses.detail
        modal = FeedbackProblemModal(
            title,
            user_input=detail,
            view=self,
            bot=self.app
        )
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Reset', style=discord.ButtonStyle.gray, emoji=discord.PartialEmoji(name='✂️'))   
    async def reset(self, interaction : discord.Interaction, _):
        embed = self.load_warning_embed(True)
        self.modal_responses = None
        self.adjust_buttons(True)
        await interaction.response.edit_message(view=self, embed=embed) 
    
    @discord.ui.button(label='Send', style=discord.ButtonStyle.green, emoji=discord.PartialEmoji(name='\N{INCOMING ENVELOPE}'))
    async def send(self, interaction : discord.Interaction, _): 
        embed = super().load_warning_embed()
        embed.title = 'Waiting For Sending...'
        embed.description = 'This will be done shortly. Please wait...'
        await interaction.response.edit_message(embed=embed, view=None)
        self.is_pressed = True
        self.stop()
        
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[Any]) -> None:
        if isinstance(error, FeedbackButtonOnCooldown):
            assert self.app.err_handler
            await self.app.err_handler.on_app_command_error(interaction, error)
        else:
            await super().on_error(interaction, error, item)
    
    async def on_timeout(self) -> None:
        await super().on_timeout()
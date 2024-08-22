from __future__ import annotations

from datetime import datetime, timedelta
from discord import (
    ButtonStyle,
    ComponentType,
    Embed,
    Interaction,
    InteractionMessage,
    PartialEmoji,
    TextStyle,
    ui
)
from discord.ext import commands
from discord.utils import format_dt, utcnow
from typing import Any, Optional
from .embed_color import interaction_with_server, failed
from .models import ModalResponse

import inspect
import re

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
        """
        Sets up button custom ids like\n
        `{View class name}:{button_label}:{interaction user id}`
        """
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
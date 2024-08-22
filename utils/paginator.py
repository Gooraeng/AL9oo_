from __future__ import annotations
from collections import deque
from discord import (
    ButtonStyle,
    Embed,
    Interaction,
    InteractionMessage,
    Member,
    ui,
    User,
    Webhook,
    WebhookMessage
)
from typing import List, Optional, Union


class T_Pagination(ui.View):
    """Generate Embed page.
    You can use it with normal or ephemeral message.\n
    Unlike F_Pagination, however, There is no "Exit" Button.
    

    Args:
        ui (_type_): _description_
    """
    def __init__(
        self,
        embeds : List[Embed] = None,
        *,
        _author : Union[Member, User] = None
    ):
        super().__init__(timeout=120)
        self._author = _author
        self._embeds = embeds
        self._current_page = 1
        self.message : Optional[InteractionMessage] = None
        
        if embeds:
            self._queue = deque(embeds)
            self._len = len(embeds)
            if self._len == 1:
                self.clear_items()
            else:
                self.first_page.disabled = True
                self.previous.disabled = True
            
            self._initial = embeds[0]
            self._queue[0].set_footer(text=f'Page : {self._current_page} / {self._len}')
            
    async def update_button(self, interaction : Interaction, *, embed : Embed):
        for i in self._queue:
            i.set_footer(text=f"Page : {self._current_page} / {self._len} ")   
        
        if self._current_page == self._len:
            self.next.disabled = True
            self.last_page.disabled = True
        else:
            self.next.disabled = False
            self.last_page.disabled = False
        
        if self._current_page == 1:
            self.first_page.disabled = True
            self.previous.disabled = True
        else:
            self.first_page.disabled = False
            self.previous.disabled = False

        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="|<", style=ButtonStyle.danger, custom_id="Tfirst")
    async def first_page(self, interaction : Interaction, _):
        self._queue.rotate(1)
        embed = self._queue[0]
        self._current_page = 1

        await self.update_button(interaction, embed=embed)

    @ui.button(label="<", style=ButtonStyle.primary, custom_id="Tprevious")
    async def previous(self, interaction : Interaction, _):
        self._queue.rotate(1)
        embed = self._queue[0]
        self._current_page -= 1
        
        await self.update_button(interaction, embed=embed)

    @ui.button(label=">", style=ButtonStyle.primary, custom_id="Tnext")
    async def next(self, interaction : Interaction, _):
        self._queue.rotate(-1)
        embed = self._queue[0]
        self._current_page += 1
        
        await self.update_button(interaction, embed=embed)

    @ui.button(label=">|", style=ButtonStyle.danger, custom_id="Tlast")
    async def last_page(self, interaction : Interaction, _):
        self._queue.rotate(-1)
        embed = self._queue[0]
        self._current_page = self._len
        
        await self.update_button(interaction, embed=embed)

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)
        
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self._author:
            return True

        embed = Embed(
            title='Oh!',
            description="I am sure you don't have permission to control other people things!",
            color=0xfe7866
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
        return False

    @property
    def initial(self) -> Embed:
        return self._initial


Embeds = List[Embed]


class FeedbackPagination(ui.View):
    """Generate Embed page.
    You can use it with normal or ephemeral message.\n
    Unlike F_Pagination, however, There is no "Exit" Button.
    

    Args:
        ui (_type_): _description_
    """
    def __init__(
        self,
        embeds : List[Embeds] = None,
        wh : Optional[Webhook] = None,
    ):
        super().__init__(timeout=None)
        self.wh = wh
        self.current_page : int = 0
        self.message : Optional[WebhookMessage] = None
        
        if embeds:
            self._set_max_pages(embeds)
            self.fill_items()
            self._initial = embeds[0]
    
    def _set_max_pages(self, embeds : List[Embeds]):
        self._len = len(embeds)
        self.embeds = {}
        for idx, embed in enumerate(embeds):
            self.embeds[idx] = embed
        return self
    
    def fill_items(self):
        self.clear_items()        
        use_last_and_first = self._len is not None and self._len >= 2
        
        if use_last_and_first :
            self.add_item(self.first_page)
            self.add_item(self.previous)
            self.add_item(self.next)
            self.add_item(self.last_page)
        self.add_item(self.go_to_numbered_page)
    
    def update_labels(self, page_num : int):
        self.first_page.disabled = page_num == 0
        
        self.go_to_current_page.label = str(page_num + 1)
        self.previous.label = str(page_num)
        self.next.label = str(page_num + 2)
        self.next.disabled = False
        self.previous.disabled = False
        self.first_page.disabled = False
        
        if self._len > 0 :
            self.last_page.disabled = (page_num + 1) >= self._len
            if (page_num + 1) >= self._len:
                self.next.disabled = True
                self.next.label = '...'
            
            if page_num == 0:
                self.previous.disabled = True
                self.previous.label = '…'
    
    async def show_checked_page(self, interaction: Interaction, page_num: int) -> None:
        try:
            if self._len is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(interaction, page_num)
            elif self._len > page_num >= 0:
                await self.show_page(interaction, page_num)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass
        
    async def show_page(self, interaction : Interaction, page_num : int) :
        self.current_page = page_num
        self.update_labels(page_num)
        if interaction.response.is_done():
            if self.message:
                await self.message.edit(embeds=self.embeds[page_num], view=self)
        else:
            await interaction.response.edit_message(embeds=self.embeds[page_num], view=self)

    @ui.button(label="|<", style=ButtonStyle.danger, custom_id="embeds_first")
    async def first_page(self, interaction : Interaction, _):
        await self.show_page(interaction, 0)
    
    @ui.button(label="Back", style=ButtonStyle.primary, custom_id="embeds_previous")
    async def previous(self, interaction : Interaction, _):
        await self.show_checked_page(interaction, self.current_page - 1)

    @ui.button(label='Current', style=ButtonStyle.gray, custom_id='before-eclipse', disabled=True)
    async def go_to_current_page(self, interaction : Interaction, _):
        pass
    
    @ui.button(label="Next", style=ButtonStyle.primary, custom_id="embeds_next")
    async def next(self, interaction : Interaction, _):
        await self.show_checked_page(interaction, self.current_page + 1)

    @ui.button(label=">|", style=ButtonStyle.danger, custom_id="embeds_last")
    async def last_page(self, interaction : Interaction, _):
        await self.show_page(interaction, self._len - 1)

    @ui.button(label="Skip to page..", style=ButtonStyle.gray, custom_id="num_page_button")
    async def go_to_numbered_page(self, interaction : Interaction, _):
        if self.message is None:
            return

        modal = NumberedPageModal(self._len)
        await interaction.response.send_modal(modal)
        timed_out = await modal.wait()

        if timed_out:
            await interaction.followup.send('Took too long', ephemeral=True)
            return
        elif self.is_finished():
            await modal.interaction.response.send_message('Took too long', ephemeral=True)
            return

        value = str(modal.page.value)
        if not value.isdigit():
            await modal.interaction.response.send_message(f'Expected a number not {value!r}', ephemeral=True)
            return

        value = int(value)
        await self.show_checked_page(modal.interaction, value - 1)
        if not modal.interaction.response.is_done():
            error = modal.page.placeholder.replace('Enter', 'Expected')  # type: ignore # Can't be None
            await modal.interaction.response.send_message(error, ephemeral=True)
    
    async def start(self):
        first_page = self.initial
        self.update_labels(0)
        self.message = await self.wh.send(view=self, embeds=first_page)
        
    @property
    def initial(self) -> Embeds:
        return self._initial


class NumberedPageModal(ui.Modal, title='Go to page'):
    page = ui.TextInput(label='Page', placeholder='Enter a number', min_length=1)

    def __init__(self, max_pages: Optional[int]) -> None:
        super().__init__()
        if max_pages is not None:
            as_string = str(max_pages)
            self.page.placeholder = f'Enter a number between 1 and {as_string}'
            self.page.max_length = len(as_string)

    async def on_submit(self, interaction: Interaction) -> None:
        self.interaction = interaction
        self.stop()
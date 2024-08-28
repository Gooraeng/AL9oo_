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
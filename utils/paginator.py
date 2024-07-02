from __future__ import annotations
from collections import deque
from discord import ButtonStyle, Embed, Interaction, ui
from typing import List
from discord.interactions import Interaction



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
        _author = None
    ):
        super().__init__(timeout=120)
        self._author = _author
        self._embeds = embeds
        self._current_page = 1
        if embeds is not None:
            self._queue = deque(embeds)
            self._initial = embeds[0]
            self._len = len(embeds)
            self._queue[0].set_footer(text=f'Page : {self._current_page} / {self._len}')
            
            self.children[0].disabled = True
            self.children[1].disabled = True

            if self._len == 1:
                self.clear_items()
    
    async def update_button(self, interaction : Interaction, *, embed : Embed):
        for i in self._queue:
            i.set_footer(text=f"Page : {self._current_page} / {self._len} ")   
        
        if self._current_page == self._len:
            self.children[2].disabled = True
            self.children[3].disabled = True
        else:
            self.children[2].disabled = False
            self.children[3].disabled = False
        
        if self._current_page == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True
        else:
            self.children[0].disabled = False
            self.children[1].disabled = False

        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="|<", style=ButtonStyle.danger, custom_id="Tfirst")
    async def first_page(self, interaction : Interaction, _):
        self._current_page = 1
        self._queue.rotate(1)
        embed = self._queue[0]

        await self.update_button(interaction, embed=embed)

    @ui.button(label="<", style=ButtonStyle.primary, custom_id="Tprevious")
    async def previous(self, interaction : Interaction, _):
        self._current_page -= 1
        self._queue.rotate(1)
        embed = self._queue[0]
        
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
        self.clear_items()
        self.stop()        

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self._author:
            return True
        
        else:
            embed = Embed(
                title='Oh!',
                description="I am sure you don't have permission to control other people things!",
                color=0xfe7866)
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return False

    @property
    def initial(self) -> Embed:
        return self._initial
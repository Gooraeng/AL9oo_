from __future__ import annotations
from discord import Button, ButtonStyle, Embed, Interaction, ui, TextStyle
from motor.core import AgnosticCollection
from typing import Any, Optional
from utils.embed_color import al9oo_point, failed

import discord


class PatchNotePublishModal(ui.Modal):
    def __init__(
        self,
        view : PatchNoteManageView,
        *,
        opt_title : Optional[str] = None,
        opt_description : Optional[str] = None
    ) -> None:
        super().__init__(
            title="Write what's new!",
            timeout=None,
        )
        self.view = view
        if not opt_title:
            opt_title = "New patch note rolled out!"
        if not opt_description:
            opt_description = ''
            
        self._title = ui.TextInput(
            label="Title",
            required=True,
            placeholder="Fill the title!",
            default=opt_title,
            min_length=1,
            max_length=70,
            style=TextStyle.short
        ) 
        self._description = ui.TextInput(
            label="Description",
            required=True,
            placeholder="Fill the description!",
            default=opt_description,
            min_length=1,
            max_length=2500,
            style=TextStyle.long
        )
        self.add_item(self._title)
        self.add_item(self._description)

    async def on_submit(self, interaction: Interaction) -> None:
        await self.view.rebind(interaction, title=self._title.value, description=self._description.value)
        
    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        return await interaction.response.send_message("There's something error", ephemeral=True)


class PatchNoteManageView(ui.View):
    def __init__(self, pnlog : AgnosticCollection):
        self.pnlog = pnlog
        super().__init__(timeout=None)
        self.initiate(False)
        self.title : Optional[str] = ''
        self.description : Optional[str] = ''
        
    def initiate(self, is_rebind : bool = True):
        self.clear_items()
        if is_rebind:
            self.add_item(self.yes)
            self.add_item(self.retry)
        else:
            self.add_item(self.write)
        self.add_item(self.cancel)
        
    async def rebind(self, interaction : Interaction, *, title : str, description : str):
        check = Embed(title="Please check what you wrote!", color=failed)
        embed = Embed(title=title, description=description, color=al9oo_point)
        embed.set_footer(text='If you decide to send patchnote press "YES"!')
        self.initiate()
        self.title = title
        self.description = description
        
        await interaction.response.edit_message(embeds=[check, embed], view=self)
        
    @ui.button(label="Yes", style=ButtonStyle.gray)
    async def yes(self, interaction : Interaction, button : Button):
        info = {
            "title" : self.title,
            "date_title" : f"[{str(interaction.created_at)[:19]}] " + self.title,
            "description" : self.description,
            "date" : interaction.created_at,
            "embed_date" : discord.utils.format_dt(interaction.created_at,style="f")
        }
        await self.pnlog.insert_one(info)

        await interaction.response.edit_message(view=None, embed=Embed(
            title="Patch Note was set successfully.", color=al9oo_point
        ))

    @ui.button(label="Retry", style= ButtonStyle.gray)
    async def retry(self, interaction : Interaction, button : Button):
        await interaction.response.send_modal(PatchNotePublishModal(
            self,
            opt_title=self.title,
            opt_description=self.description
        )) 
   
    @ui.button(label="Write Patch Note", style=ButtonStyle.blurple)
    async def write(self, interaction : Interaction, button : Button):
        await interaction.response.send_modal(PatchNotePublishModal(self))
        
    @ui.button(label="Cancel", style=ButtonStyle.danger)
    async def cancel(self, interaction : Interaction, button : Button):
        await interaction.message.delete()

    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        await interaction.response.send_message("There's something error", ephemeral=True)
        raise error
from __future__ import annotations
from discord import app_commands, Embed, Interaction, ui
from discord.ext import commands
from typing import TYPE_CHECKING, Any, List, Optional
from utils.embed_color import *

if TYPE_CHECKING:
    from al9oo import Al9oo



class JoinServer(ui.View):
    def __init__(self):
        super().__init__(timeout= None)
        self.add_item(ui.Button(label= "Join AL9oo Server!", url= "https://discord.gg/8dpAFYXk8s"))


    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral= True)



class PatchNoteViewer(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.pnlog = self.app._pnlog


    @app_commands.command(name= "patchnote", description= "Read AL9oo patch notes!")
    @app_commands.checks.cooldown(1, 60, key= lambda i : (i.guild_id, i.user.id))
    @app_commands.describe(search = "Choose patch note name!")
    @app_commands.guild_only()
    async def read_patchnotes(self, interaction : Interaction, search : Optional[str] = None):
        try:
            await interaction.response.defer(thinking= True)
            original = await interaction.original_response()
            data = await self.pnlog.find_one(sort=[('_id', -1)])
            if data is None:
                return await interaction.response.send_message(embed= Embed(
                    title= "Oh, it's empty.", color= failed,
                    description= "Let's wait a little longer for the new patch notes to come up."
                ), ephemeral= True)
            
            if search is None:
                search = data["title"]
            else:
                data = await self.pnlog.find_one({"date_title" : search})
            
            description = data["description"]
            date : str = data["embed_date"]
            embed = Embed(
                title= search, description= description, color= al9oo_point
            )
            return await original.edit(content= f"## Uploaded : {date}", embed= embed, view= JoinServer())
            
        except Exception:
            return await original.edit('Sorry, something error occured!')


    @read_patchnotes.autocomplete('search')
    async def read_note(self, interaction : Interaction, current : str) -> List[app_commands.Choice[str]]:
        cursor = self.pnlog.find().sort("_id", -1)
        data = [document["date_title"] async for document in cursor]
        
        if not data :
            return [
                app_commands.Choice(name= choice, value= choice)
                for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
            ]
            
        result = [
            app_commands.Choice(name= choice, value= choice)
            for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result)>25:
            result = result[:25]
        
        return result


    @read_patchnotes.error
    async def read_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry = error.retry_after
            if retry is None:
                pass
            else:
                await interaction.response.send_message(f"You have `{int(retry)} second(s)` for cooldownto this command.\nPlease wait!", ephemeral= True)
        else:
            pass



async def setup(app : Al9oo):
    await app.add_cog(PatchNoteViewer(app))
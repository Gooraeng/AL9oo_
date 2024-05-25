from __future__ import annotations
from discord import app_commands, Interaction, Object
from discord.ext import commands
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from al9oo import Al9oo

class Sync(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
    
    
    @app_commands.command(name= 'sync', description= '...')
    @app_commands.describe(where= 'select')
    async def run(self, interaction : Interaction, where : Literal["~"] = None):
        if interaction.user.id != 303915314062557185:
            return await interaction.response.send_message('You cannot run this command!', ephemeral= True)
        
        await interaction.response.defer(thinking= True, ephemeral= True)
        if where is None:
            synced = await self.app.tree.sync()
            return await interaction.followup.send(f"{len(synced)} command synced globally")
    
        synced = await self.app.tree.sync(guild= interaction.guild)       
        return await interaction.followup.send(f"{len(synced)} command synced here")
    

async def setup(app : Al9oo):
    await app.add_cog(Sync(app))
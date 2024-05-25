from __future__ import annotations
from discord import (
    app_commands, 
    Attachment, 
    Colour, 
    Embed, 
    Interaction, 
    Object
)
from discord.ext import commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from al9oo import Al9oo



@app_commands.default_permissions(administrator = True)
@app_commands.guilds(Object(id= 1205958300873527466))
@app_commands.guild_only()
class SetAL9ooAvatar(commands.GroupCog, name = "avatar"):
    def __init__(self, app : Al9oo) -> None:
        self.app = app


    @app_commands.command(name= "set", description= 'Set avatar with GIF file!')
    @app_commands.describe(avatar = 'Photo file only')
    async def upload_gif(self, interaction : Interaction, avatar : Attachment):
        async def send_message(message):
            embed = Embed(
                title= "", description= message, color= Colour.blurple()
            )
            await interaction.followup.send(embed= embed, ephemeral= True)
            
        await interaction.response.defer(thinking= True, ephemeral= True)
        try:
            await interaction.client.user.edit(avatar= await avatar.read())
            return await send_message(message= '✅ Uploaded Avatar and Replaced to that!')
        
        except Exception as e:
            await send_message(message= f'⚠️ Error : `{e}`')



async def setup(app : Al9oo):
    await app.add_cog(SetAL9ooAvatar(app))
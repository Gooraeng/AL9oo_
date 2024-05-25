from __future__ import annotations
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from utils.commandpermission import permissioncheck
from utils.embed_color import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from al9oo import Al9oo


class SupportLink(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app


    def check_interaction(interaction : Interaction):
        if interaction.user.id == 303915314062557185:
            return None
        return app_commands.Cooldown(1, 30.0)    


    @app_commands.command(name= 'support', description= 'Get support server link!')
    @app_commands.checks.dynamic_cooldown(check_interaction, key= lambda i : i.user.id)
    async def send_support_link(self, interaction : Interaction):
        embed = Embed(
            title= "AL9oo Support Server", description= "", color= al9oo_point, url= 'https://discord.gg/8dpAFYXk8s'
        )
        await interaction.response.send_message(embed= embed)


    @send_support_link.error
    async def ssl_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            pass
        
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction= interaction, error= error)
        
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'You have **{int(error.retry_after)}** second(s) to run this command again.', ephemeral= True)



async def setup(app : Al9oo):
    await app.add_cog(SupportLink(app))
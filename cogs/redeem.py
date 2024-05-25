from __future__ import annotations
from discord import Interaction, app_commands
from discord.ext import commands
from typing import TYPE_CHECKING
from utils.commandpermission import permissioncheck

if TYPE_CHECKING:
    from al9oo import Al9oo
    


class Redeem(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app


    def check_interaction(interaction : Interaction):
        if interaction.user.id == 303915314062557185:
            return None
        return app_commands.Cooldown(1, 30.0)    


    @app_commands.command(name= 'redeem', description= 'Send you redeem link!')
    @app_commands.checks.dynamic_cooldown(check_interaction, key= lambda i : i.user.id)
    async def send_redeem_link(self, interaction : Interaction):       
        await interaction.response.send_message('https://www.gameloft.com/redeem/asphalt-9-redeem')


    @send_redeem_link.error
    async def srl_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            pass
        
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction= interaction, error= error)
        
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'You have **{int(error.retry_after)}** second(s) to run this command again.', ephemeral= True)



async def setup(app : Al9oo):
    await app.add_cog(Redeem(app))
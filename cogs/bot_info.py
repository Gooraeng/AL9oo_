from __future__ import annotations
from discord import app_commands, Embed, Interaction, ui
from discord.ext import commands
from typing import TYPE_CHECKING
from utils.embed_color import al9oo_point

if TYPE_CHECKING:
    from al9oo import Al9oo

import asyncio



class InviteLinkView(ui.View):
    def __init__(self):
        super().__init__(timeout= None)
        self.add_item(ui.Button(label= "Go to Server", url= 'https://discord.gg/8dpAFYXk8s'))



class AL9ooInfo(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app


    def check(interaction : Interaction):
        if interaction.user.id == 303915314062557185:
            return None
        return app_commands.Cooldown(1, 60.0)    


    @app_commands.command(name= "me", description= "Show you AL9oo's small informations!")
    @app_commands.checks.dynamic_cooldown(check, key= lambda i: (i.guild_id, i.user.id))
    # @app_commands.guild_only()
    async def Status(self, interaction : Interaction):                
        await interaction.response.defer(thinking= True)

        try:
            uptime_float = (interaction.created_at - self.app.uptime).total_seconds()
            uptime = int(uptime_float)
            days = uptime // 86400
            hours = (uptime % 86400) // 3600
            minutes = (uptime % 3600) // 60
            seconds = uptime % 60
            uptime_msg = f"{days}D {hours}h {minutes}m {seconds}s"
            
            info = self.app.bot_app_info
            if info.bot_public:
                status = "Public"
            else:
                status = "Private"
            
            embed = Embed(title = "AL9oo", description= info.description, color= al9oo_point)   
            embed.add_field(name= "1. Birthday", value= str(self.app.user.created_at)[:10], inline= True)
            embed.add_field(name= "2. Status", value= status, inline= True)
            embed.add_field(name= "3. Representive Color", value= "#59E298, #8BB8E1", inline= True)
            embed.add_field(name= '4. Uptime', value= uptime_msg, inline= False)
            await interaction.followup.send(embed= embed, view= InviteLinkView())
        
        except:     
            await asyncio.sleep(5)
            await interaction.followup.send("Oops! There was / were error(s)! Please try again later", ephemeral= True)


    @Status.error
    async def status_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(content= f"### Please run after `{int(error.retry_after)}`second(s) later!", ephemeral= True)
        else: pass



async def setup(app : Al9oo):
    await app.add_cog(AL9ooInfo(app))
from __future__ import annotations
from discord import Interaction, app_commands, Embed, Interaction, ui
from discord.ext import commands
from typing import TYPE_CHECKING, List
from utils.embed_color import asphalt9, failed
from utils.commandpermission import permissioncheck
from utils.patchnote_manager import patchnotemanager

if TYPE_CHECKING:
    from al9oo import Al9oo
    


class ARNView(ui.View):
    def __init__(self):
        super().__init__(timeout= None)
        self.add_item(ui.Button(label= 'Get Alert Faster here!', url= "https://discord.gg/wrbSCPqhHH"))



class GetPatchNote(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app


    def check_interaction(interaction : Interaction):
        if interaction.user.id == 303915314062557185:
            return None
        return app_commands.Cooldown(3, 30.0)

    
    @app_commands.command(name= 'a9-releasenote', description= 'Let you know up to 25 published Release Notes!')
    @app_commands.describe(select = "Select a release note! If you don't, you get latest one.")
    @app_commands.guild_only()
    @app_commands.checks.dynamic_cooldown(check_interaction, key= lambda i :(i.guild_id, i.user.id))
    async def send_patchnote(self, interaction : Interaction, select : str = None):
        try:
            await interaction.response.defer(thinking= True)

            data = await patchnotemanager.get_all_from_json()
            view = ARNView()
            if select is None:
                a = data[0]
                embed = Embed(
                        title= a.get('title'), description= f"PUBLISHED DATE : {a.get('publish_dt')}\n_\n### {a.get('description')}", color= asphalt9, url= a.get('url')
                    )
                embed.set_image(url= a.get('thumbnail'))
                return await interaction.followup.send(embed= embed, view= view)
            
            for i in data:
                if select == i.get('title'):
                    embed = Embed(
                        title= i.get('title'), description= f"PUBLISHED DATE : {i.get('publish_dt')}\n_\n### {i.get('description')}", color= asphalt9, url= i.get('url')
                    )
                    embed.set_image(url= i.get('thumbnail'))
                    return await interaction.followup.send(embed= embed, view= view)
                
            return await interaction.followup.send('Can not Search corresponding patch notes.', ephemeral= True)

        except Exception as e:
            await interaction.followup.send(embed= Embed(
                title= "Oh! There was an error!",
                description= "Sorry, please run this command again.",
                color= failed
            ).add_field(name= "Error Type", value= e), ephemeral= True)


    @send_patchnote.autocomplete('select')
    async def releasenote_autocomplete(self, interaction : Interaction, current : str) -> List[app_commands.Choice[str]]:
        data = await patchnotemanager.get_titles_from_json()
        result = [
            app_commands.Choice(name= choice, value= choice)
            for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        if len(result) > 25:
            result = result[:25]
        
        return result
    
    
    @send_patchnote.error
    async def srl_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            pass
        
        if isinstance(error, app_commands.CommandOnCooldown):
            return await interaction.response.send_message(content= f"Be patient!\nPlease try again {int(error.retry_after)} second(s) later!",
                                                    ephemeral= True)
            
        if isinstance(error, app_commands.BotMissingPermissions):
            return await permissioncheck(interaction= interaction, error= error)
        
        else: raise error               
    


async def setup(app : Al9oo):
    await app.add_cog(GetPatchNote(app))
from __future__ import annotations
from discord import app_commands, Embed, Interaction, ui
from discord.ext import commands
from typing import TYPE_CHECKING, Any, List, Optional
from utils.commandpermission import permissioncheck
from utils.embed_color import al9oo_point, alu, failed
from utils.patchnote_manager import get_all_from_json, get_titles_from_json

if TYPE_CHECKING:
    from al9oo import Al9oo



class JoinServer(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label="Join AL9oo Server!", url="https://discord.gg/8dpAFYXk8s"))

    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral=True)


@app_commands.guild_only()
class PatchNote(commands.GroupCog, name='pn'):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.pnlog = self.app._pnlog

    def check_interaction(interaction : Interaction):
        if interaction.user.id == 303915314062557185:
            return None
        return app_commands.Cooldown(3, 30.0)
    
    @app_commands.command(name='alu', description='Let you know published ALU Release Notes! (not all)')
    @app_commands.describe(select="Select a release note! If you don't, you get latest one.")
    @app_commands.checks.dynamic_cooldown(check_interaction, key=lambda i :(i.guild_id, i.user.id))
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def send_patchnote(self, interaction : Interaction, select : str = None):
        await interaction.response.defer(thinking=True)

        try:
            data = await get_all_from_json(select)
            title = data.get('title')
            publish = data.get('publish_dt')
            description = data.get('description')
            url = data.get('url')
            thumbnail = data.get('thumbnail')
            
            embed = Embed(
                title=title, description=f"PUBLISHED DATE : {publish}\n_\n### {description}", color=alu, url=url 
            )
            embed.set_image(url=thumbnail)
            
            view = ui.View(timeout=None)
            view.add_item(
                ui.Button(
                    label='Get Alert Faster here!',
                    url="https://discord.gg/wrbSCPqhHH"
                )
            )
            
            return await interaction.followup.send(embed=embed, view=view)
        
        except Exception as e:
            await interaction.followup.send(f'Can not Search corresponding patch notes.\n{e}', ephemeral=True)

    @send_patchnote.autocomplete('select')
    async def releasenote_autocomplete(self, interaction : Interaction, current : str) -> List[app_commands.Choice[str]]:
        data = await get_titles_from_json()
        result = [
            app_commands.Choice(name=choice, value=choice)
            for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        if len(result) > 25:
            result = result[:25]
        return result

    @app_commands.command(name="algoo", description="Read AL9oo patch notes!")
    @app_commands.checks.cooldown(5, 20, key=lambda i : i.user.id)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    @app_commands.describe(search="Choose patch note name!")
    @app_commands.guild_only()
    async def read_patchnotes(self, interaction : Interaction, search : Optional[str] = None):
        try:
            await interaction.response.defer(thinking=True)
            original = await interaction.original_response()
            data = await self.pnlog.find_one(sort=[('_id', -1)])
            if data is None:
                return await interaction.response.send_message(
                    embed=Embed(
                        title="Oh, it's empty.", color=failed,
                        description="Let's wait a little longer for the new patch notes to come up."
                    ), ephemeral=True
                )
            
            if search is None:
                search = data["title"]
            else:
                data = await self.pnlog.find_one({"date_title" : search})
            
            description = data["description"]
            date : str = data["embed_date"]
            embed = Embed(
                title=search, description=description, color=al9oo_point
            )
            return await original.edit(content=f"## Uploaded : {date}", embed=embed, view=JoinServer())
            
        except Exception:
            return await original.edit('Sorry, something error occured!')

    @read_patchnotes.autocomplete('search')
    async def read_note(self, interaction : Interaction, current : str) -> List[app_commands.Choice[str]]:
        cursor = self.pnlog.find().sort("_id", -1)
        data = [document["date_title"] async for document in cursor]
        
        if not data :
            return [
                app_commands.Choice(name=choice, value=choice)
                for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
            ]
            
        result = [
            app_commands.Choice(name=choice, value=choice)
            for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result)>25:
            result = result[:25]
        return result

    @send_patchnote.error
    @read_patchnotes.error
    async def srl_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.response.send_message(embed=Embed(
                title="Oh! There was an error!",
                description="Sorry, please run this command again.",
                color=failed
            ).add_field(name="Error Type", value=error), ephemeral=True)

        elif isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                content=f"Be patient!\nYou are on cooldown for {int(error.retry_after)} second(s)!",
                ephemeral=True
            )
        
        elif isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction, error=error)

   
async def setup(app : Al9oo):
    await app.add_cog(PatchNote(app))
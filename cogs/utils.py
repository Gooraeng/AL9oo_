from __future__ import annotations
from discord import app_commands, Embed, Interaction, Message, ui
from discord.ext import commands
from discord.utils import format_dt
from utils.commandpermission import permissioncheck
from utils.embed_color import *
from typing import List, Optional, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from al9oo import Al9oo

import asyncio
import discord


exclude_cmds = (
    'admin',
    'follow',
    'help',
    'profile',
    'patch'
    
)

def check_interaction(interaction : Interaction):
    if interaction.user.id == 303915314062557185:
        return None
    return app_commands.Cooldown(1, 30.0)  


class InviteLinkView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label="Go to Server", url='https://discord.gg/8dpAFYXk8s'))


class CommandsTutorialSelect(ui.Select):
    def __init__(
        self,
        practice : Tuple[List[discord.SelectOption],
        List[str]]
    ):
        self._practice = practice[0]
        self._description = practice[1]

        super().__init__(
            placeholder="Choose Command!",
            options=self._practice,
            min_values=1,
            max_values=1,
            custom_id="tutorial"
        )

    async def callback(self, interaction: Interaction):
        a = self.values[0]
        num = 0
        for i in range(0, len(self._description)):
            if a in self._description[i][0]:                
                if self._description[i][6] == "":
                    embed = Embed(
                        title=a,
                        description=f"{self._description[i][1]}",
                        color=0x62D980
                    )
                else:
                    embed = Embed(
                        title=a,
                        description=f"{self._description[i][1]}\n({self._description[i][6]})",
                        color=0xA064FF
                    )
                
                if self._description[i][2] == "":
                    pass
                else:
                    description = self._description[i][2]
                    
                    num += 1
                    if a == "/elite" or a == "/note":
                        embed.add_field(
                            name=f"**{num}. Parameter**",
                            value=f"**(1) Parameter list**\n* {description}\n**(2) Search Sequence**\n* {self._description[i][4]}",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name=f"**{num}. Parameter**",
                            value=f"**(1) Parameter list**\n* (Essential) {description}\n**(2) Search Sequence**\n* {self._description[i][4]}",
                            inline=False
                        )
                num += 1
                embed.add_field(
                    name=f"{num}. How to use it",
                    value=f"{self._description[i][5]}",
                    inline=False
                )
                
                if self._description[i][3] != "None":
                    num += 1
                    embed.add_field(
                        name=f"{num}. AL9oo Requires Permission(s)",
                        value=f"* {self._description[i][3]}",
                        inline=False
                    )
                embed.set_footer(text="If any command doesn't execute properly, try again please.")
                
        try:
            await interaction.response.edit_message(content="", embed=embed)
        
        except :
            await interaction.response.defer(thinking=True, ephemeral=True)
            await asyncio.sleep(5)
            await interaction.followup.edit_message(content="", embed=embed)


class TutorialView(ui.View):
    def __init__(
        self,
        practice : Tuple[List[discord.SelectOption],
        List[str]]
    ):
        super().__init__(timeout=None)
        self._practice = practice
        self.add_item(CommandsTutorialSelect(self._practice))
        self.message : Optional[Message] = None

    async def on_timeout(self) -> None:
        self.clear_items()
        self.stop()
        if self.message:
            try:
                self.message.delete()
            except:
                pass


class Utils(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app

    async def configure_help(self) -> tuple[list, list]:
        def add_description(cmd : app_commands.Command, /):
            if cmd.parameters:
                temp = (f"`{parameter.display_name}` - {parameter.description}" for parameter in cmd.parameters)
                a = '\n* '.join(s for s in temp)
            else:
                a = ""
            
            permission = cmd.extras.get("permissions")
            if permission: 
                b = "\n* ".join(s for s in permission)
            else:
                b = "None"   

            sequence = cmd.extras.get("sequence")
            if sequence:
                c = sequence
            else:
                c = "Well.."
            
            howto = cmd.extras.get("howto")
            if howto:
                d = "\n".join(s for s in howto) 
            else:
                d = "* You would know how to do it!"
            
            if cmd.guild_only:
                e = "This command does NOT operate in DM."
            else:
                e = ""
            
            result.append([f"/{cmd.qualified_name}", cmd.description, a, b, c, d, e])
            options.append(
                discord.SelectOption(
                    label=cmd.qualified_name,
                    description=cmd.description
                )
            )
            
        options = []; result = []
        for cmd, cog in self.app.cogs.items():
            if cmd.lower() in exclude_cmds:
                continue 
            cmds = cog.walk_app_commands()
            for cmd in cmds:
                if cmd.name.lower() in exclude_cmds:
                    continue
                if isinstance(cmd, app_commands.Command):
                    add_description(cmd)
        return options, result
    
    @app_commands.command(name="help", description="You can know how to enjoy AL9oo!")
    @app_commands.guild_only()
    async def help(self, interaction : Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        original = await interaction.original_response()
        try:
            help = await self.configure_help()
            view = TutorialView(help)      
            view.message = await original.edit(view=view, embed=Embed(
                title="Please Choose command",
                description="This helps you use commands well!",
                colour=etc
            ))
            await view.wait()
        except Exception as e:
            await original.edit(content="Something Error Occured.")
    
    @app_commands.command(name='redeem', description='Send you redeem link!')
    @app_commands.checks.dynamic_cooldown(check_interaction, key=lambda i : i.user.id)
    async def redeem(self, interaction : Interaction):       
        await interaction.response.send_message('https://www.gameloft.com/redeem/asphalt-9-redeem')
   
    @app_commands.command(name='support', description='Get support server link!')
    @app_commands.checks.dynamic_cooldown(check_interaction, key=lambda i : i.user.id)
    async def support(self, interaction : Interaction):
        embed = Embed(
            title="AL9oo Support Server", description="", color=al9oo_point, url='https://discord.gg/8dpAFYXk8s'
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="who", description="am 'I'?")
    @app_commands.checks.dynamic_cooldown(check_interaction, key=lambda i: i.user.id)
    async def who(self, interaction : Interaction):                
        try:
            await interaction.response.defer(thinking=True)
            uptime_float = (interaction.created_at - self.app.uptime).total_seconds()
            uptime = int(uptime_float)
            days = uptime // 86400
            hours = (uptime % 86400) // 3600
            minutes = (uptime % 3600) // 60
            seconds = uptime % 60
            uptime_msg = f"{days}D {hours}h {minutes}m {seconds}s"
            
            info = await self.app.application_info()
            
            embed = Embed(title=interaction.client.user.global_name, description=info.description, color=al9oo_point)   
            embed.add_field(name="1. Birthday", value=format_dt(self.app.user.created_at, 'F'), inline=False)
            embed.add_field(name='2. Uptime', value=uptime_msg, inline=True)
            embed.add_field(name="3. Representive Color", value="#59E298, #8BB8E1", inline=True)
            
            await interaction.followup.send(embed=embed, view=InviteLinkView())
        
        except:     
            await asyncio.sleep(5)
            await interaction.edit_original_response(content="Oops! There was / were error(s)! Please try again later.")

    @help.error
    @redeem.error
    @support.error
    @who.error
    async def ssl_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction, error=error)
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'You are on cooldown for **{int(error.retry_after)}** second(s) to run this command.',
                ephemeral=True
            )


async def setup(app : Al9oo):
    await app.add_cog(Utils(app))
    
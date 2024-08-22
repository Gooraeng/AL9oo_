from __future__ import annotations
from discord import app_commands, Embed, Interaction, InteractionMessage, Permissions, ui
from discord.ext import commands
from discord.utils import format_dt, oauth_url
from utils.commandpermission import permissioncheck
from utils.common import InviteLinkView
from utils.embed_color import al9oo_point, etc
from utils.models import CommandUsageModel
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from al9oo import Al9oo

import asyncio
import inspect
import time


exclude_cmds = (
    # these are bot admin only
    'admin',
    'patch',
    'profile',
    # this cmds public
    'help',
)


def check_interaction(interaction : Interaction):
    if interaction.user.id == 303915314062557185:
        return None
    return app_commands.Cooldown(1, 30.0)  


class CommandsTutorialSelect(ui.Select):
    def __init__(self, cmds : List[CommandUsageModel]):
        super().__init__(
            placeholder="Choose Command!",
            min_values=1,
            max_values=1,
        )
        
        for cmd in cmds:
            name = cmd.name[1:]
            self.add_option(label=name, description=cmd.description)
        self.cmds = cmds

    async def callback(self, interaction : Interaction):
        cmd_name = self.values[0]
        target = None
        for cmd in self.cmds:
            if cmd_name == cmd.name[1:]:
                target = cmd
                break
        
        assert target is not None
        num = 1
        
        if target.guild_only:
            guild = "\n### This command doesn't work at DM."
            colour = 0xA064FF
        else:
            guild = ''
            colour = 0x62D980
            
        embed = Embed(
            title=target.name,
            description=f'{target.description}{guild}',
            colour=colour
        )
        
        if target.details["parameters"]:
            if target.details["sequence"]:
                sequence = f"\n**(2) Search Sequence**\n* {target.details['sequence']}"
            else:
                sequence = ""
            embed.add_field(
                name=f"{num}. Parameter",
                value=f"**(1) List**\n{target.details['parameters']}{sequence}",
                inline=False
            )
            num += 1
        
        embed.add_field(
            name=f"{num}. How to use",
            value=f"{target.details['how_to']}",
            inline=False
        )
        num += 1
        
        if target.details["permissions"]:
            embed.add_field(
                name=f"{num}. I require Permission(s)",
                value=f"{target.details['permissions']}"
            )
            num += 1
    
        if target.default_permission:
            embed.add_field(
                name=f"{num}. You need Permission(s)",
                value=f"{target.default_permission}"
            )
        
        embed.set_footer(text="Try again please if any command doesn't run properly.")
        
        try:
            await interaction.response.edit_message(content=None, embed=embed)
        
        except :
            await interaction.response.defer(thinking=True, ephemeral=True)
            await asyncio.sleep(5)
            await interaction.followup.send(content=None, embed=embed, ephemeral=True)


class TutorialView(ui.View):
    def __init__(
        self,
        cmds : List[CommandUsageModel]
    ):
        super().__init__(timeout=None)
        self.add_item(CommandsTutorialSelect(cmds))
        self.message : Optional[InteractionMessage] = None

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

    async def configure_help(self, interaction : Interaction) :
        async def add_description(cmd : app_commands.Command):
            if cmd.parameters:
                temp = []
                for parameter in cmd.parameters:
                    if parameter.required:
                        is_req = ' (Essential) '
                    else:
                        is_req = ' '
                    temp.append(f"*{is_req}`{parameter.name}` - {parameter.description}")
                a = '\n'.join(s for s in temp)
                del temp
            else:
                a = None
                
            permission = cmd.extras.get("permissions")
            if permission: 
                b = "* " + "\n* ".join(s for s in permission)
            else:
                b = None   

            sequence = cmd.extras.get("sequence")
            if sequence:
                c = sequence
            else:
                c = None
            
            howto = cmd.extras.get("howto")
            if howto:
                d = "\n".join(s for s in howto) 
            else:
                d = "* You would know how to do it!"
            
            if cmd.default_permissions and cmd.default_permissions & interaction.channel.permissions_for(interaction.user) == cmd.default_permissions:
                e = cmd.default_permissions.__qualname__.replace('_', ' ').replace('guild', 'server').title()
            else:
                e = None
                
            result.append(CommandUsageModel(
                name=f"/{cmd.qualified_name}",
                description=cmd.description,
                guild_only=cmd.guild_only,
                default_permission=e,
                details={
                    "parameters" : a,
                    "permissions" : b,
                    "sequence" : c,
                    "how_to" : d,
                }       
            ))
            
        result : List[CommandUsageModel] = []
        
        tasks = []
        for cmd, cog in self.app.cogs.items():
            if cmd.lower() in exclude_cmds:
                continue 
            cmds = cog.walk_app_commands()
            for cmd in cmds:
                if cmd.name.lower() in exclude_cmds:
                    continue
                if isinstance(cmd, app_commands.Command):
                    tasks.append(add_description(cmd))
        
        await asyncio.gather(*tasks)
        result.sort(key=lambda i : i.name)
        return result
    
    @app_commands.command(name="help", description="You can know how to enjoy AL9oo!")
    @app_commands.guild_only()
    async def help(self, interaction : Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            helps = await self.configure_help(interaction)
            view = TutorialView(helps)      
            view.message = await interaction.edit_original_response(content=None, view=view, embed=Embed(
                title="Please Choose command",
                description="This helps you use commands well!",
                colour=etc
            ))
            await view.wait()
            
        except Exception as e:
            await interaction.edit_original_response(content=e)

    @app_commands.command(name='redeem', description='Send you redeem link!')
    @app_commands.checks.dynamic_cooldown(check_interaction, key=lambda i : i.user.id)
    async def redeem(self, interaction : Interaction):       
        await interaction.response.send_message('https://www.gameloft.com/redeem/asphalt-legends-unite')
    
    @app_commands.command(description='Run this If you interested in me!')
    @app_commands.checks.dynamic_cooldown(check_interaction, key=lambda i : i.user.id)
    async def invite(self, interaction : Interaction):
        perm = Permissions.none()
        perm.read_message_history = True
        perm.read_messages = True
        perm.send_messages = True
        perm.send_messages_in_threads = True
        perm.manage_messages = True
        perm.manage_webhooks = True
        perm.attach_files = True
        perm.embed_links = True
        await interaction.response.send_message(f'<{oauth_url(self.app.client_id, permissions=perm)}>')
        
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
            view = InviteLinkView(label="Go to Server", url='https://discord.gg/8dpAFYXk8s')
            await interaction.followup.send(embed=embed, view=view)
        
        except:     
            await asyncio.sleep(5)
            await interaction.edit_original_response(content="Oops! There was / were error(s)! Please try again later.")

    @app_commands.command(name='ping', description='Pong! Checks Ping with server.')
    @app_commands.checks.dynamic_cooldown(check_interaction, key=lambda i : i.user.id)
    async def ping(self, interaction : Interaction):
        start = time.perf_counter()
       
        await interaction.response.defer(thinking=True, ephemeral=True)
        shard_id = interaction.guild.shard_id
        shard = self.app.get_shard(shard_id)
        latency = shard.latency
        
        end = time.perf_counter()
        duration = (end - start) * 1000
        
        embed = Embed(
            title='Pong!',
            description=inspect.cleandoc(
                f"""* Shard {shard_id} Ping : {int(latency*1000)}ms
                * Actual Ping : {int(duration)}ms
                """ 
            ),
            colour=al9oo_point
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
   
    @help.error
    @redeem.error
    @support.error
    @who.error
    @ping.error
    @invite.error
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
    
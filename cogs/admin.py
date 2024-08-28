from __future__ import annotations
from component.patchnote import PatchNoteManageView
from config import vaild_formats
from discord import (
    app_commands, 
    Attachment, 
    Colour, 
    Embed, 
    Interaction, 
    Object,
)
from discord.ext import commands
from typing import Any, Dict, Literal, Optional, TYPE_CHECKING
from utils.embed_color import al9oo_point
from utils.exception import InvaildFileFormat
from utils.paginator import T_Pagination

if TYPE_CHECKING:
    from al9oo import Al9oo

import asyncio
import psutil  


def buffed_cached() -> Dict[str, Any]:
    meminfo = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if parts[0] in ('Buffers:', 'Cached:', 'SwapCached:'):
                    meminfo[parts[0].rstrip(':')] = int(parts[1])
    except:
        pass
    return meminfo


def system_status() -> Embed:        
    cpu = psutil.cpu_percent(interval= 1)
    mem = psutil.virtual_memory()
    total_mem = mem.total / (1024**3)
    free_mem = mem.free / (1024**3)
    avail_mem = mem.available / (1024**3)
    
    bc_info = buffed_cached()
    buffer = bc_info.get('Buffers', 0)
    cache = bc_info.get('Cached', 0)
    # bc = (buffer + cache) / (1024**3)
    
    rows = [
        ['* CPU USAGE', f'{cpu:.0f}%'],
        ['* TOTAL', f'{total_mem:.2f} GB'],
        ['* FREE', f'{free_mem:.2f} GB'],
        ['* AVAILABLE', f'{avail_mem:.2f} GB']
    ]

    description = '```ansi\n{:<14} | {:<8}\n============================'.format('CATEGORY', 'VALUE')

    for row in rows:
        description += f'\n{row[0]:<14} | [0;34m{row[1]:<15}[0m'
    description = f"{description}```"
    
    embed = Embed(title='System Info', description=description, color=al9oo_point)
    return embed

 
@app_commands.guild_only()  
class SetAL9ooAvatar(commands.GroupCog, name='profile'):
    def __init__(self, app : Al9oo) -> None:
        self.app = app

    @app_commands.command(name='edit-me', description='Set avatar or banner!')
    @app_commands.describe(avatar='Photo file only')
    async def upload_avatar(
        self, 
        interaction : Interaction, 
        avatar : Optional[Attachment] = None,
        banner : Optional[Attachment] = None
    ):
        async def send_message(message, /):
            embed = Embed(description=message, color=Colour.blurple())
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            if (avatar and avatar.content_type not in vaild_formats) or (banner and banner.content_type not in vaild_formats):
                raise InvaildFileFormat
            
            avatar_byte = await avatar.read() if avatar else None
            banner_byte = await banner.read() if banner else None
            
            await interaction.client.user.edit(avatar=avatar_byte, banner=banner_byte)
            await send_message('✅ Edited me!')
        
        except Exception as e:
            await send_message(f'⚠️ Error : `{e}`')

  
@app_commands.guild_only()  
class PatchNotePublisher(commands.GroupCog, name='patch'):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.pnlog = self.app._pnlog

    @app_commands.command(name="publish", description="You write patch note? use it!")
    async def publish_patchnote(self, interaction : Interaction):
        view = PatchNoteManageView(self.pnlog)
        await interaction.response.send_message(view=view)

    @app_commands.command(name="list", description="Do you want to see all patch notes?")
    async def list_patchnote(self, interaction : Interaction):
        await interaction.response.defer(thinking=True)
        cursor = self.pnlog.find().sort("_id", -1)
        data = [document["date_title"] async for document in cursor]
        
        length = len(data)
        
        if length == 0:
            return await interaction.followup.send("No patch list exist.", ephemeral= True)
        
        embeds = []
        
        per_page = 15
        page, left_over = divmod(length, per_page)
        if left_over:
            page += 1
        
        for i in range(0, page):
            embed = Embed(
                title="ALL patch notes",
                description=f"## Existing Patch note : {length}",
                color= 0xff4545
            )
            for j in range(0, per_page):
                embed.add_field(
                    name=f"{(per_page*i+j)+1}. {data[per_page*i+j]}",
                    value="",
                    inline=False
                )
            embeds.append(embed)
        
        view = T_Pagination(embeds)
        view._author = interaction.user
        await interaction.followup.send(embed=view.initial, view=view, ephemeral=True)


class Admin(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.pnlog = self.app._pnlog 

    @app_commands.command(name='sysinfo', description='...')
    @app_commands.guild_only()
    async def sysinfo(self, interaction : Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            embed = system_status()
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            await asyncio.sleep(5)
            await interaction.followup.send(f"Error : {e}", ephemeral= True)
                
    @app_commands.command(name='sync-command', description='...')
    @app_commands.describe(where='select')
    @app_commands.guild_only()
    async def sync_commands(self, interaction : Interaction, where : Optional[Literal["~"]] = None):
        await interaction.response.defer(thinking=True, ephemeral=True)
        if where is None:
            synced = await self.app.tree.sync()
            await interaction.followup.send(f"{len(synced)} command synced globally")
            return
    
        synced = await self.app.tree.sync(guild=interaction.guild)  
        cmds = '\n'.join(s.name for s in synced)
        print(cmds)    
        await interaction.followup.send(f"{len(synced)} command synced here")


async def setup(app : Al9oo):
    await app.add_cog(Admin(app), guild=Object(id=1205958300873527466))
    await app.add_cog(PatchNotePublisher(app), guild=Object(id=1205958300873527466))
    await app.add_cog(SetAL9ooAvatar(app), guild=Object(id=1205958300873527466))
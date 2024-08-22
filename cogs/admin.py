from __future__ import annotations
from discord import (
    app_commands, 
    Attachment, 
    Button,
    ButtonStyle,
    Colour, 
    Embed, 
    Interaction, 
    Object,
    TextStyle,
    ui
)
from discord.ext import commands
from discord.utils import format_dt
from motor.core import AgnosticCollection
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING
from config import vaild_formats
from utils.embed_color import al9oo_point, failed
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


class FinalCheck(ui.View):
    def __init__(
        self,
        infos : List[str] = None,
        *,
        pnlog : AgnosticCollection = None
    ):
        self.infos = infos
        self.pnlog = pnlog
        super().__init__(timeout=None)
        
    @ui.button(label="Yes", style=ButtonStyle.gray, custom_id="set-patchnote")
    async def yes(self, interaction : Interaction, button : Button):
        info = {
            "title" : self.infos[0],
            "date_title" : f"[{str(interaction.created_at)[:19]}] " + self.infos[0],
            "description" : self.infos[1],
            "date" : interaction.created_at,
            "embed_date" : format_dt(interaction.created_at,style="f")
        }
        await self.pnlog.insert_one(info)

        await interaction.response.edit_message(view=None, embed=Embed(
            title="Patch Note is set", color=al9oo_point
        ))

    @ui.button(label="retry", style= ButtonStyle.gray, custom_id="retry-set-patchnote")
    async def retry(self, interaction : Interaction, button : Button):
        await interaction.response.send_modal(PatchNotePublishModal_retry(self.infos, pnlog=self.pnlog))
        
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral=True)


class PatchNotePublishModal_retry(ui.Modal):
    def __init__(
        self,
        infos : List[str] = None,
        *,
        pnlog : AgnosticCollection = None
    ) -> None:
        super().__init__(
            title="Write what's new!",
            timeout=None,
            custom_id="pub_modal_retry"
        )
        self.pnlog = pnlog
        self._title = ui.TextInput(
            label="Title",
            required=True,
            placeholder="Fill the title!",
            default=infos[0],
            custom_id="retry_publish_modal",
            style=TextStyle.short,
            min_length=1,
            max_length=70
        ) 
        self._description = ui.TextInput(
            label="Description",
            required=True,
            placeholder="Fill the description!",
            default=infos[1],
            custom_id="retry_publish_description", 
            min_length=1,
            max_length=3800,
            style=TextStyle.long
        )
        self.add_item(self._title)
        self.add_item(self._description)

    async def on_submit(self, interaction: Interaction) -> None:
        check = Embed(title="Please check what you wrote!", color=failed)
        pnote_info = [self._title.value, self._description.value]
        u_wrote = Embed(title=pnote_info[0], description=pnote_info[1], color=al9oo_point)
        
        view = FinalCheck(pnote_info, pnlog=self.pnlog)
        await interaction.response.edit_message(embeds=[check, u_wrote], view=view)

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        return await interaction.response.send_message("There's something error", ephemeral=True)


class PatchNotePublishModal(ui.Modal):
    def __init__(self, pnlog : AgnosticCollection) -> None:
        super().__init__(
            title="Write what's new!",
            timeout=None,
            custom_id="pub_modal"
        )
        self.pnlog = pnlog
        self._title = ui.TextInput(
            label="Title",
            required=True,
            placeholder="Fill the title!",
            default="New patch note rolled out!",
            custom_id="publish_title",
            min_length=1,
            max_length=70,
            style=TextStyle.short
        ) 
        self._description = ui.TextInput(
            label="Description",
            required=True,
            placeholder="Fill the description!",
            custom_id="publish_description",
            min_length=1,
            max_length=2000,
            style=TextStyle.long
        )
        self.add_item(self._title)
        self.add_item(self._description)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.message.delete()
        check = Embed(title="Please check what you wrote!", color=failed)
        pnote_info = [self._title.value, self._description.value]
        u_wrote = Embed(title=pnote_info[0], description=pnote_info[1], color=al9oo_point)
        
        view = FinalCheck(pnote_info, pnlog=self.pnlog)
        await interaction.response.send_message(embeds= [check, u_wrote], view=view)

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        return await interaction.response.send_message("There's something error", ephemeral=True)


class PatchNoteManageView(ui.View):
    def __init__(self, pnlog : AgnosticCollection):
        self.pnlog = pnlog
        super().__init__(timeout=None)
    
    @ui.button(label="Write Patch Note", style=ButtonStyle.blurple, custom_id="write-pn")
    async def write(self, interaction : Interaction, button : Button):
        await interaction.response.send_modal(PatchNotePublishModal(self.pnlog))
        
    @ui.button(label="Cancel", style=ButtonStyle.danger, custom_id="cancel-pn")
    async def cancel(self, interaction : Interaction, button : Button):
        await interaction.message.delete()

    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral=True)


class DeletePatchNoteView(ui.View):
    def __init__(
        self,
        title : str = None,
        *,
        pnlog : AgnosticCollection = None
    ):
        super().__init__(timeout=None)
        self.title = title
        self.pnlog = pnlog
        
    @ui.button(label="Yes", style=ButtonStyle.gray, custom_id="delete-patchnote")
    async def yes(self, interaction : Interaction, button : Button):
        try:
            data = await self.pnlog.find_one({"date_title" : self.title})
            if data is None:
                content = "Cannot delete this patch note!\nIt might be already deleted or it might not exist."
            else:
                await self.pnlog.delete_one({"date_title" : self.title})
                content = f"### Deleted : {self.title}"
            await interaction.response.edit_message(content=content, embed=None, view=None)
        except:
            await interaction.response.defer(thinking=True, ephemeral=True)
            await interaction.followup.send("There is something Error! Please try again!", ephemeral=True)
            
    @ui.button(label="Cancel", style=ButtonStyle.danger, custom_id="cancel-del-patchnote")
    async def no(self, interaction : Interaction, button : Button):
        await interaction.message.delete()

    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral=True)

      
@app_commands.guild_only()  
class SetAL9ooAvatar(commands.GroupCog, name='profile'):
    def __init__(self, app : Al9oo) -> None:
        self.app = app

    @app_commands.command(name='avatar', description='Set avatar!')
    @app_commands.describe(avatar='Photo file only')
    async def upload_avatar(self, interaction : Interaction, avatar : Attachment):
        async def send_message(message, /):
            embed = Embed(
                title="", description=message, color=Colour.blurple()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            if avatar.content_type not in vaild_formats:
                raise InvaildFileFormat
            
            await interaction.client.user.edit(avatar=await avatar.read())
            return await send_message('✅ Uploaded Avatar and Replaced to that!')
        
        except Exception as e:
            await send_message(f'⚠️ Error : `{e}`')

    @app_commands.command(name='banner', description='Set banner!')
    @app_commands.describe(avatar='Photo file only')
    async def upload_banner(self, interaction : Interaction, avatar : Attachment):
        async def send_message(message, /):
            embed = Embed(
                title="", description=message, color=Colour.blurple()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            if avatar.content_type.upper() not in vaild_formats:
                raise InvaildFileFormat
            
            await interaction.client.user.edit(banner=await avatar.read())
            await send_message('✅ Uploaded Banner and Replaced to that!')
            return
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
        cursor = self.pnlog.find().sort("_id", -1)
        data = [document["date_title"] async for document in cursor]
        
        length = len(data)
        
        if length == 0:
            return await interaction.response.send_message("No patch list exist.", ephemeral= True)
        
        embeds = []
        per_page = 8
        for i in range(0, (length // per_page + 1)):
            try:
                embed = Embed(
                    title="ALL patch notes",
                    description=f"## Existing Patch note : {length}",
                    color= 0xff4545
                )
                
                for j in range(0, per_page):
                    try:
                        embed.add_field(
                            name=f"{(per_page*i+j)+1}. {data[per_page*i+j]}",
                            value="",
                            inline=False
                        )
                    except:
                        break
            except:
                continue
            
            embeds.append(embed)
        
        view = T_Pagination(embeds)
        view._author = interaction.user
        await interaction.response.send_message(embed=view.initial, view=view, ephemeral=True)

    @app_commands.command(name="delete", description="Do you want to delete patch note?")
    @app_commands.describe(search="Choose patch note name!")
    async def delete_patchnote(self, interaction : Interaction, search: Optional[str] = None):
        if search is None:
            data = await self.pnlog.find_one(sort=[('_id', -1)])
        else:
            data = await self.pnlog.find_one({"date_title" : search})
        
        if not data :
            return await interaction.response.send_message('검색 불가', ephemeral=True)
        
        title = search if search else data["date_title"]
        desc = data["description"]
        
        if len(desc) > 1000:
            desc = desc[:1000] + "\n...(중략)"

        view = DeletePatchNoteView(title, pnlog=self.pnlog)
        await interaction.response.send_message(embed=Embed(
            title="Do you want to Delete this patch note?",
            description=f"### 1. Title\n* {title}\n### 2. Description\n-----------------\n* {desc}",
            color=failed
        ), view=view)
        
    @delete_patchnote.autocomplete('search')
    async def read_note(self, interaction : Interaction, current : str) -> List[app_commands.Choice[str]]:
        cursor = self.pnlog.find().sort("_id", -1)
        data = [document["date_title"] async for document in cursor]
        
        if not data :
            return [
                app_commands.Choice(name=choice, value=choice)
                for choice in data if current.lower().strip() in choice.lower().strip()
            ]
            
        result = [
            app_commands.Choice(name=choice, value=choice)
            for choice in data if current.lower().strip() in choice.lower().strip()
        ]
        
        if len(result) > 25:
            result = result[:25]
        
        return result


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
    
    @sysinfo.error
    async def err(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("You don't have permission to run this command.", ephemeral=True)
        else:
            pass


async def setup(app : Al9oo):
    await app.add_cog(Admin(app), guild=Object(id=1205958300873527466))
    await app.add_cog(PatchNotePublisher(app), guild=Object(id=1205958300873527466))
    await app.add_cog(SetAL9ooAvatar(app), guild=Object(id=1205958300873527466))
    # await app.tree.sync(guild=Object(id=1205958300873527466))
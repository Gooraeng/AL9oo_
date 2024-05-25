from __future__ import annotations
from discord import (
    app_commands,
    Embed, 
    Interaction,
    ui, 
    TextStyle, 
    Button,
    ButtonStyle,
    Object
)
from discord.ext import commands
from discord.utils import format_dt
from typing import TYPE_CHECKING, Any, List, Optional
from utils.embed_color import al9oo_point, failed
from utils.paginator import T_Pagination
from motor.core import AgnosticCollection

if TYPE_CHECKING:
    from al9oo import Al9oo    



class FinalCheck(ui.View):
    def __init__(self, *, infos : List[str] = None, pnlog : AgnosticCollection = None):
        self.infos = infos
        self.pnlog = pnlog
        super().__init__(timeout= None)

        
    @ui.button(label= "Yes", style= ButtonStyle.gray, custom_id= "set-patchnote")
    async def yes(self, interaction : Interaction, button : Button):
        info = {
            "title" : self.infos[0],
            "date_title" : f"[{str(interaction.created_at)[:19]}] " + self.infos[0],
            "description" : self.infos[1],
            "date" : interaction.created_at,
            "embed_date" : format_dt(interaction.created_at,style= "f")
        }
        await self.pnlog.insert_one(info)

        await interaction.response.edit_message(view= None, embed= Embed(
            title= "Patch Note is set", description= "", color= al9oo_point
        ))


    @ui.button(label= "retry", style= ButtonStyle.gray, custom_id= "retry-set-patchnote")
    async def retry(self, interaction : Interaction, button : Button):
        await interaction.response.send_modal(PatchNotePublishModal_retry(infos= self.infos, pnlog= self.pnlog))
        
        
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral= True)



class PatchNotePublishModal_retry(ui.Modal):
    def __init__(self, *, infos : List[str] = None, pnlog : AgnosticCollection = None) -> None:
        super().__init__(title= "Write what's new!", timeout= None, custom_id= "pub_modal_retry")
        self.pnlog = pnlog
        self._title = ui.TextInput(
            label= "Title", required= True, placeholder= "Fill the title!",
            default= infos[0], custom_id= "retry_publish_modal",
            style= TextStyle.short, min_length= 1, max_length= 70
        ) 
        self._description = ui.TextInput(
            custom_id= "retry_publish_description",
            label= "Description", required= True, placeholder= "Fill the description!", default= infos[1],
            min_length= 1, max_length= 4000, style= TextStyle.long
        )
        self.add_item(self._title)
        self.add_item(self._description)


    async def on_submit(self, interaction: Interaction) -> None:
        check = Embed(title= "Please check what you wrote!", description= "", color= failed)
        pnote_info = [self._title.value, self._description.value]
        u_wrote = Embed(title= pnote_info[0], description= pnote_info[1], color= al9oo_point)
        
        view = FinalCheck(infos= pnote_info, pnlog= self.pnlog)
        await interaction.response.edit_message(embeds= [check, u_wrote], view= view)


    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        return await interaction.response.send_message("There's something error", ephemeral= True)



class PatchNotePublishModal(ui.Modal):
    def __init__(self, *, pnlog : AgnosticCollection = None) -> None:
        super().__init__(title = "Write what's new!", timeout= None, custom_id= "pub_modal")
        self.pnlog = pnlog
        self._title = ui.TextInput(
            label= "Title", required= True, placeholder= "Fill the title!",
            default= "New patch note rolled out!",
            style= TextStyle.short, min_length= 1, max_length= 70, custom_id= "publish_title"
        ) 
        self._description = ui.TextInput(
            label= "Description", required= True, placeholder= "Fill the description!",
            min_length= 1, max_length= 2000, style= TextStyle.long, custom_id= "publish_description"
        )
        self.add_item(self._title)
        self.add_item(self._description)


    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.message.delete()
        check = Embed(title= "Please check what you wrote!", description= "", color= failed)
        pnote_info = [self._title.value, self._description.value]
        u_wrote = Embed(title= pnote_info[0], description= pnote_info[1], color= al9oo_point)
        
        view = FinalCheck(infos= pnote_info, pnlog= self.pnlog)
        await interaction.response.send_message(embeds= [check, u_wrote], view= view)


    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        return await interaction.response.send_message("There's something error", ephemeral= True)



class PatchNoteManageView(ui.View):
    def __init__(self, *, pnlog : AgnosticCollection = None):
        self.pnlog = pnlog
        super().__init__(timeout= None)
    
    @ui.button(label= "Write Patch Note", style= ButtonStyle.blurple, custom_id= "write-pn")
    async def write(self, interaction : Interaction, button : Button):
        await interaction.response.send_modal(PatchNotePublishModal(pnlog= self.pnlog))
        
    @ui.button(label= "Cancel", style= ButtonStyle.danger, custom_id= "cancel-pn")
    async def cancel(self, interaction : Interaction, button : Button):
        await interaction.message.delete()


    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral= True)



class DeletePatchNoteView(ui.View):
    def __init__(self, *, title : str = None, pnlog : AgnosticCollection = None):
        super().__init__(timeout= None)
        self.title = title
        self.pnlog = pnlog
        
    @ui.button(label= "Yes", style= ButtonStyle.gray, custom_id= "delete-patchnote")
    async def yes(self, interaction : Interaction, button : Button):
        try:
            data = await self.pnlog.find_one({"date_title" : self.title})
            if data is None:
                await interaction.response.edit_message("Cannot delete this patch note!\nIt might be already deleted or it might not exist.", embed= None, view= None)
            else:
                await self.pnlog.delete_one({"date_title" : self.title})
                await interaction.response.edit_message(f"### Deleted : {self.title}", embed= None, view= None)
        except:
            await interaction.response.defer(thinking= True, ephemeral= True)
            await interaction.followup.send("There is something Error! Please try again!", ephemeral= True)
            
    @ui.button(label= "Cancel", style= ButtonStyle.danger, custom_id= "cancel-del-patchnote")
    async def no(self, interaction : Interaction, button : Button):
        await interaction.message.delete()


    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item[Any]) -> None:
        return await interaction.response.send_message("There's something error", ephemeral= True)



@app_commands.guilds(Object(id= 1205958300873527466))        
@app_commands.guild_only()   
class PatchNotePublisher(commands.GroupCog, name = "pn"):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.pnlog = self.app._pnlog
        
    
    @app_commands.command(name= "publish", description= "You write patch note? use it!")
    async def publish_patchnote(self, interaction : Interaction):
        view = PatchNoteManageView(pnlog= self.pnlog)
        await interaction.response.send_message(view= view)


    @app_commands.command(name= "list", description= "Do you want to see all patch notes?")
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
                embed = Embed(title= "ALL patch notes", description= f"## Existing Patch note : {length}", color= 0xff4545)
                
                for j in range(0, per_page):
                    try:
                        embed.add_field(name= f"{(per_page*i+j)+1}. {data[per_page*i+j]}", value= "", inline= False)
                    except:
                        break
            except:
                continue
            
            embeds.append(embed)
        
        view = T_Pagination(embeds)
        view._author = interaction.user
        await interaction.response.send_message(embed= view.initial, view= view, ephemeral= True)


    @app_commands.command(name= "delete", description= "Do you want to delete patch note?")
    @app_commands.describe(search = "Choose patch note name!")
    async def delete_patchnote(self, interaction : Interaction, search: Optional[str] = None):
        if search is None:
            data = await self.pnlog.find_one(sort=[('_id', -1)])
            title = data["date_title"]
            desc = (data["description"])[:30] + "\n..."
            view = DeletePatchNoteView(title= title, pnlog= self.pnlog)
            await interaction.response.send_message(embed= Embed(
                title= "Do you want to Delete this patch note?",
                description= f"### 1. Title\n* {title}\n### 2. Description\n* {desc}", color= failed
            ), view= view)
            
        
    @delete_patchnote.autocomplete('search')
    async def read_note(self, interaction : Interaction, current : str) -> List[app_commands.Choice[str]]:
        cursor = self.pnlog.find().sort("_id", -1)
        data = [document["date_title"] async for document in cursor]
        
        if not data :
            return [
                app_commands.Choice(name= choice, value= choice)
                for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
            ]
            
        result = [
            app_commands.Choice(name= choice, value= choice)
            for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result) > 25:
            result = result[:25]
        
        return result
    

    
async def setup(app : Al9oo):
    await app.add_cog(PatchNotePublisher(app), guild= Object(id= 1205958300873527466))
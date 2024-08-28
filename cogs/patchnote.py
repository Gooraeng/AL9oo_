from __future__ import annotations
from discord import app_commands, Embed, Interaction, ui
from discord.ext import commands, tasks
from discord.utils import format_dt
from lxml import etree
from typing import TYPE_CHECKING, Any, List, NamedTuple, Optional, TypedDict
from utils.embed_color import al9oo_point, alu, failed

if TYPE_CHECKING:
    from al9oo import Al9oo

import datetime
import json
import io
import logging
import re


log = logging.getLogger(__name__)
parser = etree.HTMLParser()  


@staticmethod
def parse_html(html: str) -> Optional[str]:
    tree = etree.parse(io.StringIO(html), parser)
    content = tree.xpath("//script[contains(text(), 'newsArticles')]/text()")
    return content


@staticmethod
def change_to_dt(string: str):
    string = string.replace('Z', '+00:00')
    dt = datetime.datetime.fromisoformat(string)
    other = "[%s] " %str(dt)[2:10]
    other = other.replace('-', '')
    return dtModel(date=other, formatted_time=format_dt(dt, 'F'))


class dtModel(NamedTuple):
    date : str
    formatted_time : str


class ALUpatchNotes(TypedDict):
    url : str
    title : str
    description : Optional[str]
    published_at : str
    thumbnail : Optional[str]


class AL9ooPatchNotes(TypedDict):
    title : str
    date_title : str
    description : str
    embed_date : str


class JoinServer(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label="Join AL9oo Server!", url="https://discord.gg/8dpAFYXk8s"))


@app_commands.guild_only()
class PatchNote(commands.GroupCog, name='pn'):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.pnlog = self.app._pnlog
        self._alu_all_info : List[ALUpatchNotes] = []
        self._algoo_all_info : List[AL9ooPatchNotes] = []
        
        # tasks
        self.alu_process.start()
        self.algoo_process.start()

    @property
    def alu_all_info(self):
        return self._alu_all_info
    
    @alu_all_info.setter
    def alu_all_info(self, value : List[ALUpatchNotes]) :
        self._alu_all_info = value
        
    @property
    def algoo_all_info(self):
        return self._algoo_all_info
    
    @algoo_all_info.setter
    def algoo_all_info(self, value : List[AL9ooPatchNotes]):
        self._algoo_all_info = value
        
    def check_interaction(interaction : Interaction):
        if interaction.user.id == 303915314062557185:
            return None
        return app_commands.Cooldown(5, 30.0)
    
    @app_commands.command(name='alu', description='Let you know published ALU Release Notes! (not all)')
    @app_commands.describe(select="Select a release note! If you don't, you get latest one.")
    @app_commands.checks.dynamic_cooldown(check_interaction, key=lambda i : i.user.id)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def alu_patchnote(self, interaction : Interaction, select : str = None):
        await interaction.response.defer(thinking=True)

        try:
            embed = Embed(
                title="Oh, it's empty.", 
                description="Let's wait for the new patch notes.",
                color=failed,
            )
            if not self.alu_all_info:
                return await interaction.followup.send(embed=embed, ephemeral=True)
            
            data = None
            if not select:
                data = self.alu_all_info[0]
            else:
                for i in self.alu_all_info:
                    if i["title"] == select:
                        data = i
                        break
            
            if not data:
                raise Exception
            
            title = data['title']
            publish = data["published_at"] if data["published_at"] else 'NO INFO'
            description = data["description"] if data["description"] else 'NO INFO'
            url = data["url"]
            thumbnail = data["thumbnail"] if data['thumbnail'] else None
            
            embed = Embed(
                title=title, 
                description=f"PUBLISHED DATE : {publish}\n_\n### {description}",
                color=alu,
                url=url 
            )
            if thumbnail:
                embed.set_image(url=thumbnail)
            
            view = ui.View(timeout=None)
            view.add_item(
                ui.Button(
                    label='Get Alert Faster from here!',
                    url="https://discord.gg/wrbSCPqhHH"
                )
            )
            return await interaction.followup.send(embed=embed, view=view)
        
        except Exception as e:
            await interaction.followup.send(f'Can not Search corresponding patch notes.\n{e}', ephemeral=True)

    @alu_patchnote.autocomplete('select')
    async def releasenote_autocomplete(self, interaction : Interaction, current : str) -> List[app_commands.Choice[str]]:
        if not self.alu_all_info:
            return [
                app_commands.Choice(name=choice, value=choice)
                for choice in [] if current.lower() in choice.lower()
            ]
            
        data = [a["title"] for a in self.alu_all_info]
        result = [
            app_commands.Choice(name=choice, value=choice)
            for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        return result[:25]

    @app_commands.command(name="algoo", description="Read AL9oo patch notes!")
    @app_commands.checks.cooldown(5, 20, key=lambda i : i.user.id)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    @app_commands.describe(search="Choose patch note name!")
    async def algoo_patchnotes(self, interaction : Interaction, search : Optional[str] = None):
        await interaction.response.defer(thinking=True)
        try:
            embed=Embed(
                title="Oh, it's empty.", 
                description="Let's wait for the new patch notes.",
                color=failed,
            )
            if not self.algoo_all_info:
                return await interaction.followup.send(embed=embed, ephemeral=True)
            
            searched = None
            if search is None:
                searched = self.algoo_all_info[0]
            else:
                for i in self.algoo_all_info:
                    if i["date_title"] == search:
                        searched = i
                        break
            
            if not searched:
                embed.title = "I didn't find that."
                embed.description = "Please type it precisely."
                return await interaction.followup.send(embed=embed) 
            
            embed = Embed(title=searched["title"], description=searched['description'], color=al9oo_point)
            await interaction.followup.send(content=f"## Uploaded : {searched['embed_date']}", embed=embed, view=JoinServer())
            
        except Exception:
            await interaction.followup.send('Sorry, something error occured!')

    @algoo_patchnotes.autocomplete('search')
    async def read_note(self, interaction : Interaction, current : str) -> List[app_commands.Choice[str]]:
        if not self.algoo_all_info:
           return [
                app_commands.Choice(name=choice, value=choice)
                for choice in [] if current.lower() in choice.lower()
            ]
           
        data = [title["date_title"] for title in self.algoo_all_info]
        result = [
            app_commands.Choice(name=choice, value=choice)
            for choice in data if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        return result[:25]  

    @tasks.loop(minutes=10)
    async def alu_process(self):
        url = "https://asphaltlegendsunite.com/news/"
        async with self.app.session.get(url) as response:
            if response.status != 200:
                return
            html = await response.text()

        content = parse_html(html)
        
        if not content:
            log.error('아스팔트 패치노트 - newsArticles를 포함하는 스크립트를 검색 실패.')
            return
        
        content = content[0]
        alu_pattern = re.compile(r'newsArticles\\":(.*?),\\"newsArticlesMeta')
        search = alu_pattern.search(content)
        
        if search:
            result = search.group(1)
            result = re.sub(r'\\(")', r'\1', result)
            result = result.replace('\\\\', "\\")
            data = json.loads(result)
            
            final : List[ALUpatchNotes] = []
            for item in data:
                if len(final) > 25:
                    break
                
                result = change_to_dt(item["publishDate"])
                title = result.date + (item["title"]).strip() 
                if not final:
                    title = "(Latest) " + title
                    
                final.append(ALUpatchNotes(
                    url=url + item["slug"],
                    title=title,
                    description=(item["excerpt"]).strip(),
                    published_at=result.formatted_time,
                    thumbnail=item["thumbnail"]["url"]
                ))

            if not final:
                self.alu_all_info = []
            else:
                self.alu_all_info = final.copy()
        
        else:
            log.error('아스팔트 패치노트 - 필요한 데이터를 추출할 수 없음.')

    @tasks.loop(minutes=10)
    async def algoo_process(self):
        cursor = self.pnlog.find().sort("_id", -1)
        data = [
            AL9ooPatchNotes(
                title=doc['title'], 
                date_title=doc['date_title'], 
                description=doc['description'],
                embed_date=doc['embed_date']
            ) 
            async for doc in cursor
        ]
        
        if not data:
            self.algoo_all_info = []
        else:
            self.algoo_all_info = data.copy()
        
    @alu_process.before_loop
    @algoo_process.before_loop
    async def ready(self):
        await self.app.wait_until_ready()
    
   
async def setup(app : Al9oo):
    await app.add_cog(PatchNote(app))
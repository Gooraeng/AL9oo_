from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from discord import app_commands, Embed, Interaction, ui
from discord.ext import commands
from typing import List, TYPE_CHECKING, Tuple
from utils.embed_color import etc
from utils.commandpermission import permissioncheck

if TYPE_CHECKING:
    from al9oo import Al9oo
    
import asyncio
import discord



excluded_cog_names = [
    "avatar",
    "channel",
    "alert",
    "Tutorial", 
    "pn",
    "db",
    "JoinedGuildInfo",
    "SystemStatus",
    "Sync"
]



class CommandsTutorialSelect(ui.Select):
    def __init__(self, practice : Tuple[List[discord.SelectOption], List[str]]):
        self._practice = practice[0]
        self._description = practice[1]

        super().__init__(
            placeholder= "Choose Command!",
            options= self._practice,
            min_values= 1, max_values= 1, custom_id= "tutorial"
        )


    async def callback(self, interaction: Interaction):
        a = self.values[0]
        num = 0
        for i in range(0, len(self._description)):
            if a in self._description[i][0]:                
                if self._description[i][6] == "":
                    embed = Embed(
                        title= a,
                        description= f"{self._description[i][1]}",
                        color= 0x62D980
                    )
                else:
                    embed = Embed(
                        title= a,
                        description= f"{self._description[i][1]}\n({self._description[i][6]})",
                        color= 0xA064FF
                    )
                
                if self._description[i][2] == "":
                    pass
                else:
                    description = self._description[i][2]
                    
                    num += 1
                    if a == "/elite" or a == "/note":
                        embed.add_field(name= f"**{num}. Parameter**",
                                        value= f"**(1) Parameter list**\n* {description}\n**(2) Search Sequence**\n* {self._description[i][4]}",
                                        inline= False)
                    else:
                        embed.add_field(name= f"**{num}. Parameter**",
                                        value= f"**(1) Parameter list**\n* (Essential) {description}\n**(2) Search Sequence**\n* {self._description[i][4]}",
                                        inline= False)
                num += 1
                embed.add_field(name= f"{num}. How to use it",
                                value= f"{self._description[i][5]}",
                                inline= False)
                
                if self._description[i][3] != "None":
                    num += 1
                    embed.add_field(name= f"{num}. AL9oo Requires Permission(s)",
                                value= f"* {self._description[i][3]}",
                                inline= False)
                embed.set_footer(text= "If any command doesn't execute properly, try again please.")
                
        try:
            await interaction.response.edit_message(content= "", embed= embed)
        
        except :
            await interaction.response.defer(thinking= True, ephemeral= True)
            await asyncio.sleep(5)
            await interaction.followup.edit_message(content= "", embed= embed)



class TutorialView(ui.View):
    def __init__(self, practice : Tuple[List[discord.SelectOption], List[str]], /):
        super().__init__(timeout= None)
        self._practice = practice
        self.add_item(CommandsTutorialSelect(self._practice))



class Tutorial(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.executor = ThreadPoolExecutor()


    @app_commands.command(name= "help", description= "You can know how to enjoy AL9oo!")
    @app_commands.guild_only()
    async def tutorial_interaction(self, interaction : Interaction):
        async def get_help():
            help = await interaction.client.loop.run_in_executor(
                self.executor, self.help
            )
            return help

        await interaction.response.defer(thinking= True, ephemeral= True)
        original = await interaction.original_response()
        try:
            help = await get_help()
            view = TutorialView(help)      
            await original.edit(view= view, embed= Embed(
                title= "Please Choose command",
                description= "This helps you use commands well!",
                colour= etc
            ))

        except Exception as e:
            await original.edit(content= "Something Error Occured.")
            raise e


    @tutorial_interaction.error
    async def tutorial_interaction_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction= interaction, error= error)
    
    
    def help(self) -> tuple[list, list]:
        options = []; result = []
        bot = self.app
        for name in bot.cogs:
            if name in excluded_cog_names:
                continue        
            temp = []
            cog = bot.get_cog(name)
            co = cog.get_app_commands()[0]
            
            # parameters
            if co.parameters:
                for i in range(0, len(co.parameters)):
                    temp.append(f"`{co.parameters[i].display_name}` - {co.parameters[i].description}")
                a = "\n* ".join(s for s in temp)
            else:
                a = ""
                
            # get list
            per = co.extras.get("permissions") 
            if per is None:
                b = "None"
            else:
                b = "\n* ".join(s for s in per)
            
            # sequence
            sequence = co.extras.get("sequence")
            if sequence is None:
                c = "Well.."
            else:
                c = sequence
                
            # howtouse
            howto = co.extras.get("howto")
            if howto is None:
                d = "* You would know how to do it!"
            else:
                d = "\n".join(s for s in howto)
                
            # is guild?
            if co.guild_only == True:
                e = "This command does NOT operate in DM."
            else:
                e = ""
                
            # result 
            result.append([f"/{co.name}", co.description, a, b, c, d, e])
            
            # options
            options.append(discord.SelectOption(
                label= f"/{co.name}",
                description= f"{co.description}"))
            
        return options, result


async def setup(app : Al9oo):
    await app.add_cog(Tutorial(app))
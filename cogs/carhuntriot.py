from __future__ import annotations
from discord import app_commands, Interaction, Embed
from discord.ext import commands
from utils.manage_tool import Carhunt as c
from typing import List, TYPE_CHECKING
from utils import embed_color
from utils.commandpermission import permissioncheck

if TYPE_CHECKING:
    from al9oo import Al9oo



class CarHunt(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app


    @app_commands.command(name='carhunt', description= 'You can watch Car hunt Riot videos!',
                          extras= {"permissions" : ["Send Messages",
                                                    "Read Message History",
                                                    "Embed Links"],
                                   }
                          )
    @app_commands.describe(car = 'What do you want to find?')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(send_messages = True,
                                             read_message_history = True,
                                             embed_links = True)
    async def car_hunt_search(self, interaction : Interaction, car : str):
        try:  
            car = car.upper()
            car_data = await c.car_name()
            map_data = await c.area()
            lap_time_data = await c.laptime()
            link_data = await c.link()

            if car in car_data:
                # 입력한 차량명과 일치하는 차량의 인덱스 넘버 변수 선언 
                CarName_found = car_data.index(car)
                return await interaction.response.send_message(f'```Car    : {car_data[CarName_found]}\nMap    : {map_data[CarName_found]}\nRecord : {lap_time_data[CarName_found]}```{link_data[CarName_found]}')

            else:
                embed1 = Embed(title='❗ Warning', description=f'No info < {car} >', colour= embed_color.failed)
                return await interaction.response.send_message('', embed= embed1, ephemeral= True)
        
        except Exception as e:
            print(e)


    @car_hunt_search.error
    async def car_hunt_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction= interaction, error= error)
        
        else: pass


    @car_hunt_search.autocomplete('car')
    async def chs_autocpletion(self,
        interaction : Interaction,
        current : str
    ) -> List[app_commands.Choice[str]]:
        car_name = await c.car_name()
        
        result = [
            app_commands.Choice(name= choice, value= choice)
            for choice in car_name if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result) > 8:
            result = result[:8]
            
        return result



async def setup(app : Al9oo):
    await app.add_cog(CarHunt(app))
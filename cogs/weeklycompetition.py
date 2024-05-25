from __future__ import annotations
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from typing import Optional, List, TYPE_CHECKING
from utils.manage_tool import Weeklycompetition as w
from utils.embed_color import failed
from utils.commandpermission import permissioncheck

if TYPE_CHECKING:
    from al9oo import Al9oo
    
import asyncio
import discord
import numpy



class Weeklycompetion(commands.Cog):
    def __init__(self, app : Al9oo):
        self.app = app


    @app_commands.command(name= 'weekly', description= 'Let you know Weekly Competition references!',
                          extras= {"permissions" : ["Send Messages",
                                                    "Read Message History",
                                                    "Embed Links"],
                                   "sequence" : "`map` -> `car`",
                                   "howto" : ["**[Way 1]**\n* Search `map` and execute.",
                                            "**[Way 2]**\n* Search `map`. Then, selectable `car` list will come out. So, Choose it and execute."]}
                        )
    @app_commands.describe(area= 'Choose map!', car_name= 'What car do you want to find?')
    @app_commands.rename(area= 'map', car_name= 'car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(send_messages = True,
                                             read_message_history = True,
                                             embed_links = True)
    async def weeklycompete(self, interaction: Interaction, area : str, car_name : Optional[str] = None):        
        try:
            map_data = await w.area()
            car_data = await w.car_name()
            lap_time_data = await w.laptime()
            link_data = await w.link()
            
            map_arr = numpy.array(map_data); car_arr = numpy.array(car_data)
                
            pure_map_data = list(set(map_data))
            pure_car_data = list(set(car_data))
            
            if car_name is None and area in pure_map_data:
                try:
                    rest_list_1 = list(filter(lambda x: map_data[x] == area, range(len(map_data))))

                    car_name_none_embed = Embed(title= f"<:yt:1178651795472527401>  {area}", description= "", colour= 0xFF0000)
                    for i in range(len(rest_list_1)):
                        car_name_none_embed.add_field(name= "", value= f"[- `({lap_time_data[rest_list_1[i]]})` {car_data[rest_list_1[i]]}]({link_data[rest_list_1[i]]})\n\n", inline= False)

                    return await interaction.response.send_message(embed= car_name_none_embed)
                    
                except:
                    await interaction.response.defer(thinking= True, ephemeral= True)
                    await asyncio.sleep(5)
                    return await interaction.followup.send(embed= car_name_none_embed, ephemeral= True)
            
            if car_name in pure_car_data and area in pure_map_data:
                car_name = car_name.upper()
                
                map_arr_where = numpy.where(map_arr == area)
                car_arr_where = numpy.where(car_arr == car_name)
                same_num_list = int(numpy.intersect1d(map_arr_where, car_arr_where))
                
                if area == map_data[same_num_list] and car_name == car_data[same_num_list]:
                    return await interaction.response.send_message(f'```Car    : {car_data[same_num_list]}\nMap    : {map_data[same_num_list]}\nRecord : {lap_time_data[same_num_list]}```{link_data[same_num_list]}')
                return

        # 오류(알맞지 않은 입력) - 임베드 1 출력
        except:
            embed1 = Embed(title='Oops!', description=f'Sometthing went go wrong. Please try again later.',colour= failed)             
            embed1.add_field(name= 'You Searched :', value= f'{area} / {car_name}')
            embed1.add_field(name='',value='**<Warning>** This message will be deleted in 10 seconds!', inline=False)  
            return await interaction.response.send_message('', embed= embed1, ephemeral= True, delete_after=10)


    @weeklycompete.error
    async def weeklycompete_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            pass
        elif isinstance(error, discord.HTTPException):
            pass
        elif isinstance(error, discord.NotFound):
            pass
        elif isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction= interaction, error= error)  
        else : raise error


    @weeklycompete.autocomplete(name= 'area')
    async def area_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:
        # 리스트 선언
        map_data = await w.area()
        
        # emp_list 내 존재하는 중복 요소 제거
        filetered = list(set(map_data))
        
        result1 = [
            app_commands.Choice(name=choice,value=choice)
            for choice in filetered if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result1) > 8:
            result1 = result1[:8]
            
        return result1

            
    @weeklycompete.autocomplete(name='car_name')
    async def car_autocompletion(
        self,
        interaction : Interaction,
        current : str, 
    ) -> List[app_commands.Choice[str]]:
        
        # 리스트 선언
        map_data = await w.area()
        car_data = await w.car_name()

        aa = list(interaction.namespace.__dict__.values())
        
        rest_list = list(filter(lambda x: map_data[x] == str(aa[0]), range(len(map_data))))
         
        emp_list = [car_data[rest_list[i]] for i in range(len(rest_list))]

        result2 = [
            app_commands.Choice(name=choice,value=choice)
            for choice in emp_list if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result2) > 10:
            result2 = result2[:10]
            
        return result2



async def setup(app : Al9oo):
    await app.add_cog(Weeklycompetion(app))
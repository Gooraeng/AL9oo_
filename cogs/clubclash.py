from __future__ import annotations
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from typing import List, TYPE_CHECKING
from utils.manage_tool import Clubclash as c
from utils.embed_color import failed
from utils.paginator import T_Pagination
from utils.commandpermission import permissioncheck

if TYPE_CHECKING:
    from al9oo import Al9oo

import numpy



class ClubClash(commands.Cog):
    def __init__(self, app : Al9oo):
        self.app = app

    
    @app_commands.command(name='clash', description='Check Club Clash references!',
                          extras= {"permissions" : ["Send Messages",
                                                    "Read Message History",
                                                    "Embed Links"],
                                   "sequence" : "`map` -> `class` -> `car`",
                                   "howto" : ["**[Way 1]**\n* Search `map` and execute.",
                                            "**[Way 2]**\n* Search `map`. Then, selectable `class` list will come out. So, Choose it and execute.",
                                            "**[Way 3]**\n* Same way with Way 2 except for executing. Just select `car` and execute!"]}
                          )
    @app_commands.describe(area = 'Search Map what you looking for!', car_class = 'Choose Class!', car_name = "What's car do you find?")
    @app_commands.rename(area = 'map', car_class = 'class', car_name = 'car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(send_messages = True,
                                             read_message_history = True,
                                             embed_links = True)
    async def clashes(self, interaction: Interaction, area : str, car_class : str = None, car_name : str = None):
        try:
            # ./utils/manage_tool.py 참고
            map_data = await c.area()
            class_data = await c.car_class()
            car_data = await c.car_name()
            link_data = await c.link()
            lap_time_data = await c.laptime()
            
            # 임베드 1 선언 (오류)
            pure_map_data = list(set(map_data))
            pure_class_data = list(set(class_data))
            pure_car_data = list(set(car_data))
            
            if area in pure_map_data and car_class is None and car_name is None:
                area_list = list(filter(lambda x: map_data[x] == area, range(len(map_data))))
            
                embeds = []                
                emp_list_1 = [car_data[area_list[x]] for x in range(0, len(area_list))]
                emp_list_2 = [class_data[area_list[x]] for x in range(0, len(area_list))]
                emp_list_3 = [lap_time_data[area_list[x]] for x in range(0, len(area_list))]
                emp_list_4 = [link_data[area_list[x]] for x in range(0, len(area_list))]
                    
                true_class_data = list(set(emp_list_2)); true_class_data.sort()
                
                for j in range(0, len(true_class_data)):
                    embed = Embed(title= f'<:yt:1178651795472527401>  {area}', description= f"{true_class_data[j]} CLASS", colour= 0xff0000)
                    num = 1
                    for i in range(0, len(area_list)):
                        if emp_list_2[i] == true_class_data[j]:
                            name = emp_list_1[i]
                            record = emp_list_3[i]
                            link = emp_list_4[i]
                            embed.add_field(name= f"{num}. {name}", value= f"[- {record}]({link})", inline= False)
                            num += 1     
                    embeds.append(embed)

                view = T_Pagination(embeds)
                view._author = interaction.user
                del map_data, class_data, car_data, link_data, lap_time_data 
                return await interaction.response.send_message(embed=view.initial, view= view)

            if area in pure_map_data and car_class in pure_class_data and car_name is None:
                car_class = car_class.upper()
                car_name_none_embed = Embed(title= f"<:yt:1178651795472527401>  {area}", description= f"{car_class} CLASS", colour= 0xFF0000)
        
                rest_list_1 = list(filter(lambda x: map_data[x] == area, range(len(map_data))))
            
                for i in range(len(rest_list_1)):
                    if class_data[rest_list_1[i]]== car_class:
                        car_name_none_embed.add_field(name= "", value= f"[- `({lap_time_data[rest_list_1[i]]})` {car_data[rest_list_1[i]]}]({link_data[rest_list_1[i]]})\n\n", inline= False)
                return await interaction.response.send_message(embed= car_name_none_embed)
            
            if area in pure_map_data and car_class in pure_class_data and car_name in pure_car_data:
                area_arr = numpy.array(map_data); car_name_arr = numpy.array(car_data)
                area_search = numpy.where(area_arr == area); car_name_search = numpy.where(car_name_arr == car_name)
                same2 = int(numpy.intersect1d(area_search, car_name_search))
                
                car_name = car_name.upper()
                # 정상 실행
                if area == map_data[same2] and car_class == class_data[same2] and car_name == car_data[same2]:
                    return await interaction.response.send_message(f'```Car    : {car_data[same2]}\nMap    : {map_data[same2]}\nRecord : {lap_time_data[same2]}```{link_data[same2]}')  
                    
                # 임베드 1 출력
                else:
                    return await interaction.response.send_message('', embed= embed1, ephemeral= True, delete_after=10)

        # 오류 관리 - 임베드 1 출력 
        except Exception:
            embed1 = Embed(title= 'Oops!', description= f'Something went wrong. Please try again later!',colour= failed)
            embed1.add_field(name='You searched :', value= f'{area} / {car_class} / {car_name}', inline=False)    
            embed1.add_field(name='', value= '**<Warning>** This message will be deleted in 10 seconds!', inline=False)  
            await interaction.response.send_message('', embed= embed1, ephemeral= True, delete_after=10)


    @clashes.error
    async def clashes_error_handling(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            pass
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction= interaction, error= error)
        else : pass
        
        
    @clashes.autocomplete('area')
    async def area_autocompletion(
        self,
        interaciton : Interaction,
        current : str,
    ) -> List[app_commands.Choice[str]]:
        # 차량 리스트 선언
        map_data = await c.area()
        # 겹치는 차량 리스트가 존재하고, 리스트 검색 시 이를 허용하지 않게 하기 위한
        # set을 이용하여 겹치는 차량이 없는 새 리스트 선언
        filtered = list(set(map_data))

        result1 = [
            app_commands.Choice(name=choice, value=choice)
            for choice in filtered if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
    
        if len(result1) > 6:
            result1 = result1[:6]
            
        return result1 
    
    
    @clashes.autocomplete('car_class')
    async def class_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:
        
        # 리스트 선언
        map_data = await c.area()
        class_data = await c.car_class()
        
        # area_autocompletion을 통해 찾으려는 맵과 관련된 요소를 불러옴.
        # 여기선 딕셔너리를 이용하여 불러옴 >> dict_values(['Sacred Heart', ''])
        # 리스트로 변환
        aa = list(interaction.namespace.__dict__.values())
        
        # 검색된 맵의 행들을 인덱스로 가지는 리스트를 선언함
        # 이 때, map_data와 aa의 value가 일치하도록 필터링 (aa[0])
        rest_list = list(filter(lambda x: map_data[x] == str(aa[0]), range(len(map_data))))
        
        emp_list = [class_data[rest_list[i]] for i in range(len(rest_list))]
        
        # emp_list 내 존재하는 중복 요소 제거
        filetered = list(set(emp_list))
        
        result2 = [
            app_commands.Choice(name= choice,value= choice)
            for choice in filetered if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        return result2

        
    @clashes.autocomplete(name='car_name')
    async def car_autocompletion(
        self,
        interaction : Interaction,
        current : str, 
    ) -> List[app_commands.Choice[str]]:
        # 리스트 선언
        map_data = await c.area()
        class_data = await c.car_class()
        car_data = await c.car_name()
        
        # class_autocompletion의 결과와 연동이 어려워 같은 방법 반복
        aa = list(interaction.namespace.__dict__.values())
        rest_list_1 = list(filter(lambda x: map_data[x] == str(aa[0]), range(len(map_data))))
             
        emp_list = [
            car_data[rest_list_1[i]]
            for i in range(len(rest_list_1)) if class_data[rest_list_1[i]]== str(aa[1])
        ]
                
        result3 = [
            app_commands.Choice(name=choice, value=choice)
            for choice in emp_list if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result3) > 25:
            result3 = result3[:25]
            
        return result3
    
    
            
async def setup(app : Al9oo):
    await app.add_cog(ClubClash(app))
from __future__ import annotations
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from typing import Literal, List, Optional, TYPE_CHECKING
from utils.manage_tool import Elite as E
from utils.paginator import T_Pagination
from utils.embed_color import failed
from utils.commandpermission import permissioncheck

if TYPE_CHECKING:
    from al9oo import Al9oo
    
import numpy



class Elitecup(commands.Cog):
    def __init__(self, app : Al9oo):
        self.app = app


    @app_commands.command(name='elite', description='Let you know elite cup reference!',
                          extras= {"permissions" : ["Send Messages",
                                                    "Read Message History",
                                                    "Embed Links"],
                                   "sequence" : "`class` -> `car`",
                                   "howto" : ["**[Way 1]**\n* Select `class` and execute.",
                                            "**[Way 2]**\n* Select `class`. Then, selectable `car` list will come out. So, Choose it and execute."]}
                          )
    @app_commands.describe(class_type = 'What type of class?', car_name ='whats the car name?')
    @app_commands.rename(class_type = 'class', car_name = 'car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(send_messages = True,
                                             read_message_history = True,
                                             embed_links = True)
    async def elite(self, interaction: Interaction, class_type : Literal["S", "A", "B", "C"] = None, car_name : Optional[str] = None):         
        def add_searched(embed : Embed, /):
            embed.add_field(name= 'Searched', value= f'{class_type} / {car_name}')                           
            embed.add_field(name='', value='**<Warning>** This message will be deleted in 10 seconds!', inline=False) 
            return embed

        # ./utils/manage_tool.py 참고
        class_data = await E.car_class()
        map_data = await E.area()
        car_data = await E.car_name()
        lap_time_data = await E.laptime()
        link_data = await E.link()
                
        embed1 = Embed(title= 'Oops!', description= f'Something went wrong! Please retry later.', colour= failed)
        
        if car_name is None and class_type is None:
            try:
                class_array = numpy.array(class_data)
                embeds = []                
                true_class_data = list(set(class_data)); true_class_data.sort()

                for j in range(0, len(true_class_data)):
                    class_where = numpy.where(class_array == true_class_data[j])
                    class_where = class_where[0].tolist()
                    
                    embed = Embed(title= f"<:yt:1178651795472527401>  Elite {true_class_data[j]}", description= f'{map_data[class_where[0]]}',colour= 0xff0000)
                    
                    for i in range(0, len(class_where)):
                        embed.add_field(name= f'{i + 1}. {car_data[class_where[i]]}', value= f'[- {lap_time_data[class_where[i]]}]({link_data[class_where[i]]})', inline= False)

                    embeds.append(embed)

                view = T_Pagination(embeds)
                view._author = interaction.user
                
                await interaction.response.send_message(embed= view.initial, view= view)
            
            except Exception:
                return await interaction.response.send_message(embed= embed1, ephemeral= True, delete_after= 10)
                  
        if class_type is not None and car_name is None:        
            try:
                rest_list_1 = list(filter(lambda x: class_data[x] == class_type, range(len(class_data))))
                
                car_name_none_embed = Embed(title= f"<:yt:1178651795472527401>  Elite {class_type}",
                                            description= f"{map_data[rest_list_1[0]]}",
                                            colour= 0xFF0000)
            
                for i in range(len(rest_list_1)):
                    car_name_none_embed.add_field(name= "", value= f"[- `({lap_time_data[rest_list_1[i]]})` {car_data[rest_list_1[i]]}]({link_data[rest_list_1[i]]})\n\n", inline= False)

                return await interaction.response.send_message(embed= car_name_none_embed)
                
            except Exception:
                embed1 = add_searched(embed1)
                return await interaction.response.send_message('', embed= embed1, ephemeral= True, delete_after=10)
        
        if class_type is not None and car_name is not None:
            try:
                class_arr = numpy.array(class_data)
                car_arr = numpy.array(car_data)
                map_arr_where = numpy.where(class_arr == class_type)
                car_arr_where = numpy.where(car_arr == car_name)
                same_num_list = int(numpy.intersect1d(map_arr_where, car_arr_where))
                car_name = car_name.upper()
                
                # 정상 실행
                if class_type == class_data[same_num_list]:
                    if car_name == car_data[same_num_list]:
                        await interaction.response.send_message(f'```Car    : {car_data[same_num_list]}\nMap    : {map_data[same_num_list]}\nRecord : {lap_time_data[same_num_list]}```{link_data[same_num_list]}') 
                    else:
                        await interaction.response.send_message('', embed= embed1, ephemeral= True, delete_after=10)

                # 오류(알맞지 않은 입력) - 임베드 1 출력
                else:
                    await interaction.response.send_message('', embed= embed1, ephemeral= True, delete_after=10)

            # 오류(알맞지 않은 입력) - 임베드 1 출력 
            except Exception:
                embed1 = add_searched(embed1)
                return await interaction.response.send_message('', embed= embed1, ephemeral= True, delete_after=10)


    @elite.error
    async def elite_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            pass
        
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction= interaction, error= error)
                
                    
    @elite.autocomplete(name= 'car_name')
    async def area_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:            
        # 리스트 선언
        class_type_data = await E.car_class()
        car_data = await E.car_name()
        
        # class_type_autocompletion을 통해 찾으려는 맵과 관련된 요소를 불러옴.
        # 여기선 딕셔너리를 이용하여 불러옴 >> dict_values(['Weekly Competition', ''])
        # 리스트로 변환
        aa = list(interaction.namespace.__dict__.values())
        
        # 검색된 맵의 행들을 인덱스로 가지는 리스트를 선언함
        # 이 때, map_data와 aa의 value가 일치하도록 필터링 (aa[0])
        rest_list = list(filter(lambda x: class_type_data[x] == str(aa[0]), range(len(class_type_data))))
           
        emp_list = [car_data[rest_list[i]] for i in range(len(rest_list))]
        
        # emp_list 내 존재하는 중복 요소 제거
        filetered = list(set(emp_list))
        
        result2 = [
            app_commands.Choice(name=choice,value=choice)
            for choice in filetered if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result2) > 25:
            result2 = result2[:25]
            
        return result2

        

async def setup(app : Al9oo):
    await app.add_cog(Elitecup(app))
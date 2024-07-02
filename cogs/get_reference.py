from __future__ import annotations
from discord import app_commands, Interaction, Embed
from discord.ext import commands
from typing import List, Literal, Optional, TYPE_CHECKING
from utils.commandpermission import permissioncheck
from utils.embed_color import *
from utils.paginator import T_Pagination

if TYPE_CHECKING:
    from al9oo import Al9oo

import asyncio
import numpy


class Reference(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        
        # 레퍼런스 변수
        self.carhunt_carname = self.app.carhunt_CAR_NAME
        self.carhunt_map = self.app.carhunt_AREA
        self.carhunt_laptime = self.app.carhunt_LAP_TIME
        self.carhunt_link = self.app.carhunt_LINK
        
        self.clash_class = self.app.clash_CLASS
        self.clash_carname = self.app.clash_CAR_NAME
        self.clash_map = self.app.clash_AREA
        self.clash_laptime = self.app.clash_LAP_TIME
        self.clash_link = self.app.clash_LINK
        
        self.elite_class = self.app.elite_CLASS
        self.elite_carname = self.app.elite_CAR_NAME
        self.elite_map = self.app.elite_AREA
        self.elite_laptime = self.app.elite_LAP_TIME
        self.elite_link = self.app.elite_LINK
        
        self.weekly_carname = self.app.weekly_CAR_NAME
        self.weekly_map = self.app.weekly_AREA
        self.weekly_laptime = self.app.weekly_LAP_TIME
        self.weekly_link = self.app.weekly_LINK

    @app_commands.command(
        description='You can watch Car hunt Riot videos!',
        extras={"permissions" :["Embed Links"]}
    )
    @app_commands.describe(car='What do you want to find?')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def carhunt(self, interaction : Interaction, car : str):
        try:  
            car = car.upper()
            car_data = self.carhunt_carname
            map_data = self.carhunt_map
            lap_time_data = self.carhunt_laptime
            link_data = self.carhunt_link

            if car in car_data:
                # 입력한 차량명과 일치하는 차량의 인덱스 넘버 변수 선언 
                CarName_found = car_data.index(car)
                return await interaction.response.send_message(f'```Car    : {car_data[CarName_found]}\nMap    : {map_data[CarName_found]}\nRecord : {lap_time_data[CarName_found]}```{link_data[CarName_found]}')
            else:
                embed1 = Embed(title='❗ Warning', description=f'No info < {car} >', colour=failed)
                return await interaction.response.send_message('', embed=embed1, ephemeral=True)
        
        except Exception as e:
            print(e)

    @carhunt.autocomplete('car')
    async def chs_autocpletion(self,
        interaction : Interaction,
        current : str
    ) -> List[app_commands.Choice[str]]:
        car_name = self.carhunt_carname
        
        result = [
            app_commands.Choice(name=choice, value=choice)
            for choice in car_name if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result) > 8:
            result = result[:8]
            
        return result
    
    @app_commands.command(
        description='Check Club Clash references!',
        extras={
            "permissions" : ["Embed Links"],
            "howto" : [
                "**[Way 1]**\n* Search `map` and execute.",
                "**[Way 2]**\n* Search `map`. Then, selectable `class` list will come out. So, Choose it and execute.",
                "**[Way 3]**\n* Same way with Way 2 except for executing. Just select `car` and execute!"
            ],
            "sequence" : "`map` -> `class` -> `car`",
        }
    )
    @app_commands.describe(
        area='Search Map what you looking for!',
        car_class='Choose Class!',
        car_name="What's car do you find?"
    )
    @app_commands.rename(area='map', car_class='class', car_name='car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def clash(self, interaction: Interaction, area : str, car_class : str = None, car_name : str = None):
        try:
            # ./utils/manage_tool.py 참고
            map_data = self.clash_map
            class_data = self.clash_class
            car_data = self.clash_carname
            link_data = self.clash_link
            lap_time_data = self.clash_laptime
            
            # 임베드 1 선언 (오류)
            pure_map_data = list(set(map_data))
            pure_class_data = list(set(class_data))
            pure_car_data = list(set(car_data))
            
            if area in pure_map_data and car_class is None and car_name is None:
                area_list = list(filter(lambda x: map_data[x]==area, range(len(map_data))))
            
                embeds = []                
                emp_list_1 = [car_data[area_list[x]] for x in range(0, len(area_list))]
                emp_list_2 = [class_data[area_list[x]] for x in range(0, len(area_list))]
                emp_list_3 = [lap_time_data[area_list[x]] for x in range(0, len(area_list))]
                emp_list_4 = [link_data[area_list[x]] for x in range(0, len(area_list))]
                    
                true_class_data = list(set(emp_list_2)); true_class_data.sort()
                
                for j in range(0, len(true_class_data)):
                    embed = Embed(
                        title=f'<:yt:1178651795472527401>  {area}',
                        description= f"{true_class_data[j]} CLASS",
                        colour=0xff0000
                    )
                    num = 1
                    for i in range(0, len(area_list)):
                        if emp_list_2[i] == true_class_data[j]:
                            name = emp_list_1[i]
                            record = emp_list_3[i]
                            link = emp_list_4[i]
                            embed.add_field(
                                name=f"{num}. {name}",
                                value=f"[- {record}]({link})",
                                inline=False
                            )
                            num += 1     
                    embeds.append(embed)

                view = T_Pagination(embeds)
                view._author = interaction.user
                del map_data, class_data, car_data, link_data, lap_time_data 
                await interaction.response.send_message(embed=view.initial, view=view)
                await view.wait()
                return
            
            if area in pure_map_data and car_class in pure_class_data and car_name is None:
                car_class = car_class.upper()
                car_name_none_embed = Embed(title= f"<:yt:1178651795472527401>  {area}", description=f"{car_class} CLASS", colour=0xFF0000)
        
                rest_list_1 = list(filter(lambda x: map_data[x]==area, range(len(map_data))))
            
                for i in range(len(rest_list_1)):
                    if class_data[rest_list_1[i]]== car_class:
                        car_name_none_embed.add_field(
                            name="",
                            value=f"[- `({lap_time_data[rest_list_1[i]]})` {car_data[rest_list_1[i]]}]({link_data[rest_list_1[i]]})\n\n",
                            inline=False
                        )
                return await interaction.response.send_message(embed=car_name_none_embed)
            
            if area in pure_map_data and car_class in pure_class_data and car_name in pure_car_data:
                area_arr = numpy.array(map_data); car_name_arr = numpy.array(car_data)
                area_search = numpy.where(area_arr==area); car_name_search = numpy.where(car_name_arr==car_name)
                same2 = int(numpy.intersect1d(area_search, car_name_search))
                
                car_name = car_name.upper()
                # 정상 실행
                if area == map_data[same2] and car_class == class_data[same2] and car_name == car_data[same2]:
                    return await interaction.response.send_message(f'```Car    : {car_data[same2]}\nMap    : {map_data[same2]}\nRecord : {lap_time_data[same2]}```{link_data[same2]}')  
                    
                # 임베드 1 출력
                else:
                    return await interaction.response.send_message('', embed=embed1, ephemeral=True, delete_after=10)

        # 오류 관리 - 임베드 1 출력 
        except Exception:
            embed1 = Embed(title='Oops!', description=f'Something went wrong. Please try again later!',colour=failed)
            embed1.add_field(name='You searched :', value=f'{area} / {car_class} / {car_name}', inline=False)    
            embed1.add_field(name='', value='**<Warning>** This message will be deleted in 10 seconds!', inline=False)  
            await interaction.response.send_message('', embed=embed1, ephemeral=True, delete_after=10)       
        
    @clash.autocomplete('area')
    async def area_autocompletion(
        self,
        interaciton : Interaction,
        current : str,
    ) -> List[app_commands.Choice[str]]:
        filtered = list(set(self.clash_map))

        result1 = [
            app_commands.Choice(name=choice, value=choice)
            for choice in filtered if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
    
        if len(result1) > 6:
            result1 = result1[:6] 
        return result1 
    
    @clash.autocomplete('car_class')
    async def class_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:
        
        # 리스트 선언
        map_data = self.clash_map
        class_data = self.clash_class
        
        # area_autocompletion을 통해 찾으려는 맵과 관련된 요소를 불러옴.
        # 여기선 딕셔너리를 이용하여 불러옴 >> dict_values(['Sacred Heart', ''])
        # 리스트로 변환
        aa = list(interaction.namespace.__dict__.values())
        
        # 검색된 맵의 행들을 인덱스로 가지는 리스트를 선언함
        # 이 때, map_data와 aa의 value가 일치하도록 필터링 (aa[0])
        rest_list = list(filter(lambda x: map_data[x]==str(aa[0]), range(len(map_data))))
        emp_list = [class_data[rest_list[i]] for i in range(len(rest_list))]
        
        # emp_list 내 존재하는 중복 요소 제거
        filetered = list(set(emp_list))
        
        result2 = [
            app_commands.Choice(name=choice,value=choice)
            for choice in filetered if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        return result2
        
    @clash.autocomplete(name='car_name')
    async def car_autocompletion(
        self,
        interaction : Interaction,
        current : str, 
    ) -> List[app_commands.Choice[str]]:
        # 리스트 선언
        map_data = self.clash_map
        class_data = self.clash_class
        car_data = self.clash_carname
        
        # class_autocompletion의 결과와 연동이 어려워 같은 방법 반복
        aa = list(interaction.namespace.__dict__.values())
        rest_list_1 = list(filter(lambda x: map_data[x]==str(aa[0]), range(len(map_data))))
             
        emp_list = [
            car_data[rest_list_1[i]]
            for i in range(len(rest_list_1)) if class_data[rest_list_1[i]]==str(aa[1])
        ]
                
        result3 = [
            app_commands.Choice(name=choice, value=choice)
            for choice in emp_list if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result3) > 25:
            result3 = result3[:25]
        return result3 

    @app_commands.command(
        description='Let you know elite cup reference!',
        extras={
            "permissions" : ["Embed Links"],
            "howto" : [
                "**[Way 1]**\n* Select `class` and execute.",
                "**[Way 2]**\n* Select `class`. Then, selectable `car` list will come out. So, Choose it and execute."
            ],
            "sequence" : "`class` -> `car`",
        }
    )
    @app_commands.describe(class_type='What type of class?', car_name='whats the car name?')
    @app_commands.rename(class_type='class', car_name='car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def elite(self, interaction: Interaction, class_type : Literal["S", "A", "B", "C"] = None, car_name : Optional[str] = None):         
        def add_searched(embed : Embed, /):
            embed.add_field(name='Searched', value=f'{class_type} / {car_name}')                           
            embed.add_field(name='', value='**<Warning>** This message will be deleted in 10 seconds!', inline=False) 
            return embed

        # ./utils/manage_tool.py 참고
        class_data = self.elite_class
        map_data = self.elite_map
        car_data = self.elite_carname
        lap_time_data = self.elite_laptime
        link_data = self.elite_link
                
        embed1 = Embed(title='Oops!', description=f'Something went wrong! Please retry later.', colour=failed)
        
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
                        embed.add_field(
                            name=f'{i + 1}. {car_data[class_where[i]]}',
                            value=f'[- {lap_time_data[class_where[i]]}]({link_data[class_where[i]]})',
                            inline=False
                        )

                    embeds.append(embed)

                view = T_Pagination(embeds)
                view._author = interaction.user
                await interaction.response.send_message(embed=view.initial, view=view)
                await view.wait()

            except Exception:
                return await interaction.response.send_message(embed=embed1, ephemeral=True, delete_after=10)
                  
        if class_type is not None and car_name is None:        
            try:
                rest_list_1 = list(filter(lambda x: class_data[x]==class_type, range(len(class_data))))
                
                car_name_none_embed = Embed(
                    title=f"<:yt:1178651795472527401>  Elite {class_type}",
                    description=f"{map_data[rest_list_1[0]]}",
                    colour=0xFF0000
                )
            
                for i in range(len(rest_list_1)):
                    car_name_none_embed.add_field(
                        name="",
                        value=f"[- `({lap_time_data[rest_list_1[i]]})` {car_data[rest_list_1[i]]}]({link_data[rest_list_1[i]]})\n\n",
                        inline=False
                    )

                return await interaction.response.send_message(embed=car_name_none_embed)
                
            except Exception:
                embed1 = add_searched(embed1)
                return await interaction.response.send_message('', embed=embed1, ephemeral=True, delete_after=10)
        
        if class_type is not None and car_name is not None:
            try:
                class_arr = numpy.array(class_data)
                car_arr = numpy.array(car_data)
                map_arr_where = numpy.where(class_arr==class_type)
                car_arr_where = numpy.where(car_arr==car_name)
                same_num_list = int(numpy.intersect1d(map_arr_where, car_arr_where))
                car_name = car_name.upper()
                
                # 정상 실행
                if class_type == class_data[same_num_list]:
                    if car_name == car_data[same_num_list]:
                        await interaction.response.send_message(f'```Car    : {car_data[same_num_list]}\nMap    : {map_data[same_num_list]}\nRecord : {lap_time_data[same_num_list]}```{link_data[same_num_list]}') 
                    else:
                        await interaction.response.send_message('', embed=embed1, ephemeral=True, delete_after=10)

                # 오류(알맞지 않은 입력) - 임베드 1 출력
                else:
                    await interaction.response.send_message('', embed=embed1, ephemeral=True, delete_after=10)

            # 오류(알맞지 않은 입력) - 임베드 1 출력 
            except Exception:
                embed1 = add_searched(embed1)
                return await interaction.response.send_message('', embed=embed1, ephemeral=True, delete_after=10)     
                    
    @elite.autocomplete('car_name')
    async def area_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:            
        # 리스트 선언
        class_type_data = self.elite_class
        car_data = self.elite_carname
        
        # class_type_autocompletion을 통해 찾으려는 맵과 관련된 요소를 불러옴.
        # 여기선 딕셔너리를 이용하여 불러옴 >> dict_values(['Weekly Competition', ''])
        # 리스트로 변환
        aa = list(interaction.namespace.__dict__.values())
        # 검색된 맵의 행들을 인덱스로 가지는 리스트를 선언함
        # 이 때, map_data와 aa의 value가 일치하도록 필터링 (aa[0])
        rest_list = list(filter(lambda x: class_type_data[x]==str(aa[0]), range(len(class_type_data))))
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
    
    @app_commands.command(
        description='Let you know Weekly Competition references!',
        extras= {
            "permissions" : ["Embed Links"],
            "howto" : [
                "**[Way 1]**\n* Search `map` and execute.",
                "**[Way 2]**\n* Search `map`. Then, selectable `car` list will come out. So, Choose it and execute."
            ],
            "sequence" : "`map` -> `car`",
        }
    )
    @app_commands.describe(area='Choose map!', car_name='What car do you want to find?')
    @app_commands.rename(area='map', car_name='car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def weekly(self, interaction: Interaction, area : str, car_name : Optional[str] = None):        
        try:
            map_data = self.weekly_map
            car_data = self.weekly_carname
            lap_time_data = self.weekly_laptime
            link_data = self.weekly_link
            
            map_arr = numpy.array(map_data); car_arr = numpy.array(car_data)
                
            pure_map_data = list(set(map_data))
            pure_car_data = list(set(car_data))
            
            if car_name is None and area in pure_map_data:
                try:
                    rest_list_1 = list(filter(lambda x: map_data[x]==area, range(len(map_data))))

                    car_name_none_embed = Embed(
                        title=f"<:yt:1178651795472527401>  {area}",
                        colour=0xFF0000
                    )
                    for i in range(len(rest_list_1)):
                        car_name_none_embed.add_field(
                            name="",
                            value=f"[- `({lap_time_data[rest_list_1[i]]})` {car_data[rest_list_1[i]]}]({link_data[rest_list_1[i]]})\n\n",
                            inline=False
                        )

                    return await interaction.response.send_message(embed=car_name_none_embed)
                    
                except:
                    await interaction.response.defer(thinking=True, ephemeral=True)
                    await asyncio.sleep(5)
                    return await interaction.followup.send(embed=car_name_none_embed, ephemeral=True)
            
            if car_name in pure_car_data and area in pure_map_data:
                car_name = car_name.upper()
                
                map_arr_where = numpy.where(map_arr==area)
                car_arr_where = numpy.where(car_arr==car_name)
                same_num_list = int(numpy.intersect1d(map_arr_where, car_arr_where))
                
                if area == map_data[same_num_list] and car_name == car_data[same_num_list]:
                    return await interaction.response.send_message(f'```Car    : {car_data[same_num_list]}\nMap    : {map_data[same_num_list]}\nRecord : {lap_time_data[same_num_list]}```{link_data[same_num_list]}')
                return

        # 오류(알맞지 않은 입력) - 임베드 1 출력
        except:
            embed1 = Embed(title='Oops!', description=f'Sometthing went go wrong. Please try again later.',colour=failed)             
            embed1.add_field(name='You Searched :', value= f'{area} / {car_name}')
            embed1.add_field(name='',value='**<Warning>** This message will be deleted in 10 seconds!', inline=False)  
            return await interaction.response.send_message('', embed=embed1, ephemeral=True, delete_after=10)

    @weekly.autocomplete(name= 'area')
    async def area_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:        
        # emp_list 내 존재하는 중복 요소 제거
        filetered = list(set(self.weekly_map))
        
        result1 = [
            app_commands.Choice(name=choice,value=choice)
            for choice in filetered if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result1) > 8:
            result1 = result1[:8]
            
        return result1
    
    @weekly.autocomplete(name='car_name')
    async def car_autocompletion(
        self,
        interaction : Interaction,
        current : str, 
    ) -> List[app_commands.Choice[str]]:
        
        # 리스트 선언
        map_data = self.weekly_map
        car_data = self.weekly_carname

        aa = list(interaction.namespace.__dict__.values())
        
        rest_list = list(filter(lambda x: map_data[x]==str(aa[0]), range(len(map_data))))
         
        emp_list = [car_data[rest_list[i]] for i in range(len(rest_list))]

        result2 = [
            app_commands.Choice(name=choice,value=choice)
            for choice in emp_list if current.lower().replace(" ", "") in choice.lower().replace(" ", "")
        ]
        
        if len(result2) > 10:
            result2 = result2[:10]
            
        return result2 

    @carhunt.error
    @clash.error
    @elite.error
    @weekly.error
    async def weeklycompete_error(self, interaction : Interaction, error : app_commands.AppCommandError):
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction=interaction, error=error)  
        else : raise error


async def setup(app : Al9oo):
    await app.add_cog(Reference(app))